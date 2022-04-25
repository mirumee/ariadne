import asyncio
from typing import Dict, cast, Optional, Any, AsyncGenerator, List
from inspect import isawaitable

from graphql import GraphQLError, GraphQLSchema
from graphql.language import OperationType

from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

from ...format_error import format_error
from ...logger import log_error
from ...graphql import subscribe, validate_data, parse_query
from ...utils import get_operation_type
from ...types import (
    Operation,
    OnConnect,
    OnDisconnect,
    OnOperation,
    OnComplete,
    WebSocketConnectionError,
    ContextValue,
    ErrorFormatter,
    RootValue,
    ValidationRules,
    Extensions,
    Middlewares,
)
from .graphql_base import GraphQLWebsocketBase

# Note: Confusingly, the subscriptions-transport-ws library
# calls its WebSocket subprotocol graphql-ws,
# and the graphql-ws library calls its subprotocol graphql-transport-ws!


class GraphQLWS(GraphQLWebsocketBase):
    """Implementation of the (older) graphql-ws subprotocol from the
    subscriptions-transport-ws library
    https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md
    """

    PROTOCOL = "graphql-ws"

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
        schema: GraphQLSchema,
        websocket: WebSocket,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
        on_connect: Optional[OnConnect] = None,
        on_disconnect: Optional[OnDisconnect] = None,
        on_operation: Optional[OnOperation] = None,
        on_complete: Optional[OnComplete] = None,
        keepalive: float = None,
        **_,
    ):
        super().__init__()
        self.context_value = context_value
        self.root_value = root_value
        self.validation_rules = validation_rules
        self.debug = debug
        self.introspection = introspection
        self.logger = logger
        self.error_formatter = error_formatter
        self.extensions = extensions
        self.middleware = middleware
        self.schema = schema

        # websocket specific attributes
        self.websocket = websocket
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_operation = on_operation
        self.on_complete = on_complete

        # GraphQLWS specific attributes
        self.keepalive = keepalive

    async def handle_websocket(self) -> None:
        operations: Dict[str, Operation] = {}
        await self.websocket.accept("graphql-ws")
        try:
            while WebSocketState.DISCONNECTED not in (
                self.websocket.client_state,
                self.websocket.application_state,
            ):
                message = await self.websocket.receive_json()
                await self.handle_websocket_message(message, operations)
        except WebSocketDisconnect:
            pass
        finally:
            for operation_id, operation in list(operations.items()):
                await self.stop_websocket_operation(operation)
                del operations[operation_id]

            try:
                if self.on_disconnect:
                    result = self.on_disconnect(self.websocket)
                    if result and isawaitable(result):
                        await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

    async def handle_websocket_message(
        self,
        message: dict,
        operations: Dict[str, Operation],
    ):
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GraphQLWS.GQL_CONNECTION_INIT:
            await self.handle_websocket_connection_init_message(message)
        elif message_type == GraphQLWS.GQL_CONNECTION_TERMINATE:
            await self.handle_websocket_connection_terminate_message()
        elif message_type == GraphQLWS.GQL_START:
            await self.process_single_message(
                message.get("payload"), operation_id, operations
            )
        elif message_type == GraphQLWS.GQL_STOP:
            if operation_id in operations:
                await self.stop_websocket_operation(operations[operation_id])
                del operations[operation_id]

    async def process_single_message(
        self,
        data: Any,
        operation_id: str,
        operations: Dict[str, Operation],
    ) -> None:
        validate_data(data)

        try:
            graphql_document = parse_query(data.get("query"))
        except GraphQLError as error:
            log_error(error, self.logger)
            await self.websocket.send_json(
                {
                    "type": GraphQLWS.GQL_ERROR,
                    "id": operation_id,
                    "payload": self.error_formatter(error, self.debug),
                }
            )
            return
        operation_type = get_operation_type(graphql_document, data.get("operationName"))

        if operation_type == OperationType.SUBSCRIPTION:
            await self.start_websocket_operation(data, operation_id, operations)
        else:
            _, result = await self.execute_graphql_query(self.websocket, data)
            await self.websocket.send_json(
                {"type": GraphQLWS.GQL_DATA, "id": operation_id, "payload": result}
            )

    async def handle_websocket_connection_init_message(self, message: dict):
        try:
            if self.on_connect:
                result = self.on_connect(self.websocket, message.get("payload"))
                if result and isawaitable(result):
                    await result

            await self.websocket.send_json({"type": GraphQLWS.GQL_CONNECTION_ACK})
            asyncio.ensure_future(self.keep_websocket_alive())
        except Exception as error:
            log_error(error, self.logger)

            if isinstance(error, WebSocketConnectionError):
                payload = error.payload  # pylint: disable=no-member
            else:
                payload = {"message": "Unexpected error has occurred."}

            await self.websocket.send_json(
                {"type": GraphQLWS.GQL_CONNECTION_ERROR, "payload": payload}
            )
            await self.websocket.close()

    async def handle_websocket_connection_terminate_message(
        self,
    ):
        await self.websocket.close()

    async def keep_websocket_alive(
        self,
    ):
        if not self.keepalive:
            return
        while self.websocket.application_state != WebSocketState.DISCONNECTED:
            try:
                await self.websocket.send_json(
                    {"type": GraphQLWS.GQL_CONNECTION_KEEP_ALIVE}
                )
            except WebSocketDisconnect:
                return
            await asyncio.sleep(self.keepalive)

    async def start_websocket_operation(
        self,
        data: Any,
        operation_id: str,
        operations: Dict[str, Operation],
    ):
        context_value = await self.get_context_for_request(self.websocket)

        success, results = await subscribe(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            validation_rules=self.validation_rules,
            debug=self.debug,
            introspection=self.introspection,
            logger=self.logger,
            error_formatter=self.error_formatter,
        )

        if not success:
            results = cast(List[dict], results)
            await self.websocket.send_json(
                {"type": GraphQLWS.GQL_ERROR, "id": operation_id, "payload": results[0]}
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
                    result = self.on_operation(self.websocket, operations[operation_id])
                    if result and isawaitable(result):
                        await result
                except Exception as error:
                    if not isinstance(error, GraphQLError):
                        error = GraphQLError(str(error), original_error=error)
                    log_error(error, self.logger)

            asyncio.ensure_future(self.observe_async_results(results, operation_id))

    async def stop_websocket_operation(self, operation: Operation):
        if self.on_complete:
            try:
                result = self.on_complete(self.websocket, operation)
                if result and isawaitable(result):
                    await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

        await operation.generator.aclose()

    async def observe_async_results(
        self, results: AsyncGenerator, operation_id: str
    ) -> None:
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
                await self.websocket.send_json(
                    {"type": GraphQLWS.GQL_DATA, "id": operation_id, "payload": payload}
                )
        except Exception as error:
            if not isinstance(error, GraphQLError):
                error = GraphQLError(str(error), original_error=error)
            log_error(error, self.logger)
            payload = {"errors": [self.error_formatter(error, self.debug)]}
            await self.websocket.send_json(
                {"type": GraphQLWS.GQL_DATA, "id": operation_id, "payload": payload}
            )

        if WebSocketState.DISCONNECTED not in (
            self.websocket.client_state,
            self.websocket.application_state,
        ):
            await self.websocket.send_json(
                {"type": GraphQLWS.GQL_COMPLETE, "id": operation_id}
            )
