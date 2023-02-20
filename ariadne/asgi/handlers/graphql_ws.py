import asyncio
from inspect import isawaitable
from typing import Any, AsyncGenerator, Dict, List, Optional, cast

from graphql import DocumentNode, GraphQLError
from graphql.language import OperationType
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from ...graphql import parse_query, subscribe, validate_data
from ...logger import log_error
from ...types import (
    Operation,
    WebSocketConnectionError,
)
from ...utils import get_operation_type
from .base import GraphQLWebsocketHandler

# Note: Confusingly, the subscriptions-transport-ws library
# calls its WebSocket subprotocol graphql-ws,
# and the graphql-ws library calls its subprotocol graphql-transport-ws!


class GraphQLWSHandler(GraphQLWebsocketHandler):
    """Implementation of the (older) graphql-ws subprotocol from the
    subscriptions-transport-ws library.

    For more details see it's GH page:

    https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md
    """

    keepalive: Optional[float]

    GQL_CONNECTION_INIT = "connection_init"  # Client -> Server
    GQL_CONNECTION_ACK = "connection_ack"  # Server -> Client
    GQL_CONNECTION_ERROR = "connection_error"  # Server -> Client

    # NOTE: The keep alive message type does not follow the standard due to connection optimizations
    GQL_CONNECTION_KEEP_ALIVE = "ka"  # Server -> Client

    GQL_CONNECTION_TERMINATE = "connection_terminate"  # Client -> Server
    GQL_START = "start"  # Client -> Server
    GQL_DATA = "data"  # Server -> Client
    GQL_ERROR = "error"  # Server -> Client
    GQL_COMPLETE = "complete"  # Server -> Client
    GQL_STOP = "stop"  # Client -> Server

    def __init__(
        self,
        *args,
        keepalive: Optional[float] = None,
        **kwargs,
    ) -> None:
        """Initializes the websocket handler.

        # Optional arguments

        `keepalive`: a `float` with time frequency for sending the keep-alive
        messages to clients with open websocket connections. `1.0` is 1 second.
        If set to `None` or `0`, no keep-alive messages are sent.
        Defaults to `None`.
        """

        super().__init__(*args, **kwargs)
        self.keepalive = keepalive

    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """An entrypoint for the GraphQL WebSocket handler.

        This method is called by the Ariadne ASGI GraphQL application to handle
        the websocket connections.

        It creates the `starlette.websockets.WebSocket` instance and calls
        `handle_websocket` method with it.

        # Required arguments

        `scope`: The connection scope information, a dictionary that contains
        at least a type key specifying the protocol that is incoming.

        `receive`: an awaitable callable that will yield a new event dictionary
        when one is available.

        `send`: an awaitable callable taking a single event dictionary as a
        positional argument that will return once the send has been completed
        or the connection has been closed.

        Details about the arguments and their usage are described in the
        ASGI specification:

        https://asgi.readthedocs.io/en/latest/specs/main.html
        """
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        await self.handle_websocket(websocket)

    async def handle_websocket(self, websocket: WebSocket):
        """Handle GraphQL the WebSocket connection.

        Is called by the `handle` method and `handle_websocket` method of the
        ASGI GraphQL application.

        # Required arguments:

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.
        """
        operations: Dict[str, Operation] = {}
        await websocket.accept("graphql-ws")
        try:
            while WebSocketState.DISCONNECTED not in (
                websocket.client_state,
                websocket.application_state,
            ):
                message = await websocket.receive_json()
                await self.handle_websocket_message(websocket, message, operations)
        except WebSocketDisconnect:
            pass
        finally:
            for operation_id, operation in list(operations.items()):
                await self.stop_websocket_operation(websocket, operation)
                del operations[operation_id]

            try:
                if self.on_disconnect:
                    result = self.on_disconnect(websocket)
                    if result and isawaitable(result):
                        await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

    async def handle_websocket_message(
        self,
        websocket: WebSocket,
        message: dict,
        operations: Dict[str, Operation],
    ):
        """Handles new message from websocket connection.

        # Required arguments

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.

        `message`: a `dict` with message payload.

        `operations`: a `dict` with currently active GraphQL operations.
        """
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GraphQLWSHandler.GQL_CONNECTION_INIT:
            await self.handle_websocket_connection_init_message(websocket, message)
        elif message_type == GraphQLWSHandler.GQL_CONNECTION_TERMINATE:
            await self.handle_websocket_connection_terminate_message(websocket)
        elif message_type == GraphQLWSHandler.GQL_START:
            await self.process_single_message(
                websocket, message.get("payload"), operation_id, operations
            )
        elif message_type == GraphQLWSHandler.GQL_STOP:
            if operation_id in operations:
                await self.stop_websocket_operation(websocket, operations[operation_id])
                del operations[operation_id]

    async def process_single_message(
        self,
        websocket: WebSocket,
        data: Any,
        operation_id: str,
        operations: Dict[str, Operation],
    ) -> None:
        """Processes websocket message containing new GraphQL operation.

        # Required arguments

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.

        `data`: a `dict` with message's payload.

        `operation_id`: a `str` with an ID of new operation.

        `operations`: a `dict` with currently active GraphQL operations.
        """

        validate_data(data)
        context_value = await self.get_context_for_request(websocket, data)

        try:
            query_document = parse_query(context_value, self.query_parser, data)
        except GraphQLError as error:
            log_error(error, self.logger)
            await websocket.send_json(
                {
                    "type": GraphQLWSHandler.GQL_ERROR,
                    "id": operation_id,
                    "payload": self.error_formatter(error, self.debug),
                }
            )
            return

        operation_type = get_operation_type(query_document, data.get("operationName"))

        if operation_type == OperationType.SUBSCRIPTION:
            await self.start_websocket_operation(
                websocket,
                data,
                context_value,
                query_document,
                operation_id,
                operations,
            )
        else:
            if self.http_handler is None:
                raise TypeError(
                    "http_handler is not set, call configure method to initialize it"
                )
            _, result = await self.http_handler.execute_graphql_query(websocket, data)
            await websocket.send_json(
                {
                    "type": GraphQLWSHandler.GQL_DATA,
                    "id": operation_id,
                    "payload": result,
                }
            )

    async def handle_websocket_connection_init_message(
        self, websocket: WebSocket, message: dict
    ):
        """Handles `connection_init` websocket message.

        Initializes new websocket instance.

        # Required arguments

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.

        `message`: a `dict` with message's payload.
        """
        try:
            if self.on_connect:
                result = self.on_connect(websocket, message.get("payload"))
                if result and isawaitable(result):
                    await result

            await websocket.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_ACK})
            asyncio.ensure_future(self.keep_websocket_alive(websocket))
        except Exception as error:
            log_error(error, self.logger)

            if isinstance(error, WebSocketConnectionError):
                payload = error.payload  # pylint: disable=no-member
            else:
                payload = {"message": "Unexpected error has occurred."}

            await websocket.send_json(
                {"type": GraphQLWSHandler.GQL_CONNECTION_ERROR, "payload": payload}
            )
            await websocket.close()

    async def handle_websocket_connection_terminate_message(
        self,
        websocket: WebSocket,
    ):
        """Handles `terminate` websocket message.

        Closes open websocket connection.

        # Required arguments

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.
        """
        await websocket.close()

    async def keep_websocket_alive(self, websocket: WebSocket):
        if not self.keepalive:
            return
        while websocket.application_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.send_json(
                    {"type": GraphQLWSHandler.GQL_CONNECTION_KEEP_ALIVE}
                )
            except WebSocketDisconnect:
                return
            await asyncio.sleep(self.keepalive)

    async def start_websocket_operation(
        self,
        websocket: WebSocket,
        data: Any,
        context_value: Any,
        query_document: DocumentNode,
        operation_id: str,
        operations: Dict[str, Operation],
    ):
        if self.schema is None:
            raise TypeError("schema is not set, call configure method to initialize it")

        success, results = await subscribe(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            query_document=query_document,
            validation_rules=self.validation_rules,
            debug=self.debug,
            introspection=self.introspection,
            logger=self.logger,
            error_formatter=self.error_formatter,
        )

        if not success:
            results = cast(List[dict], results)
            await websocket.send_json(
                {
                    "type": GraphQLWSHandler.GQL_ERROR,
                    "id": operation_id,
                    "payload": results[0],
                }
            )
        else:
            results = cast(AsyncGenerator, results)
            operations[operation_id] = Operation(
                id=operation_id,
                name=data.get("operationName"),
                generator=results,
            )

            if self.on_operation:
                try:
                    result = self.on_operation(websocket, operations[operation_id])
                    if result and isawaitable(result):
                        await result
                except Exception as error:
                    if not isinstance(error, GraphQLError):
                        error = GraphQLError(str(error), original_error=error)
                    log_error(error, self.logger)

            asyncio.ensure_future(
                self.observe_async_results(websocket, results, operation_id)
            )

    async def stop_websocket_operation(
        self,
        websocket: WebSocket,
        operation: Operation,
    ):
        """Stops specified GraphQL operation for given connection.

        # Required arguments

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.

        `operation`: an `Operation` to stop.
        """
        if self.on_complete:
            try:
                result = self.on_complete(websocket, operation)
                if result and isawaitable(result):
                    await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

        await operation.generator.aclose()

    async def observe_async_results(
        self,
        websocket: WebSocket,
        results: AsyncGenerator,
        operation_id: str,
    ) -> None:
        """Converts results from Ariadne's `subscribe` generator into websocket
        messages it next sends to the client.

        # Required arguments

        `websocket`: the `WebSocket` instance from Starlette or FastAPI.

        `results`: the `AsyncGenerator` returned from Ariadne's
        `subscribe` function.

        `operation_id`: a `str` with id of operation.
        """
        try:
            async for result in results:
                payload = {}
                if result.data:
                    payload["data"] = result.data
                if result.errors:
                    for error in result.errors:
                        log_error(error, self.logger)
                    payload["errors"] = [
                        self.error_formatter(error, self.debug)
                        for error in result.errors
                    ]
                await websocket.send_json(
                    {
                        "type": GraphQLWSHandler.GQL_DATA,
                        "id": operation_id,
                        "payload": payload,
                    }
                )
        except Exception as error:
            if not isinstance(error, GraphQLError):
                error = GraphQLError(str(error), original_error=error)
            log_error(error, self.logger)
            payload = {"errors": [self.error_formatter(error, self.debug)]}
            await websocket.send_json(
                {
                    "type": GraphQLWSHandler.GQL_DATA,
                    "id": operation_id,
                    "payload": payload,
                }
            )

        if WebSocketState.DISCONNECTED not in (
            websocket.client_state,
            websocket.application_state,
        ):
            await websocket.send_json(
                {"type": GraphQLWSHandler.GQL_COMPLETE, "id": operation_id}
            )
