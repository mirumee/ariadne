import asyncio
from contextlib import suppress
from datetime import timedelta
from inspect import isawaitable
from typing import Any, AsyncGenerator, Dict, List, Optional, cast

from graphql import GraphQLError
from graphql.language import OperationType
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from ...graphql import subscribe, parse_query, validate_data
from ...logger import log_error
from ...types import (
    ExecutionResult,
    Operation,
)
from ...utils import get_operation_type
from .base import GraphQLWebsocketHandler


class ClientContext:
    def __init__(self) -> None:
        self.connection_acknowledged: bool = False
        self.connection_init_timeout_task: Optional[asyncio.Task] = None
        self.connection_init_received: bool = False
        self.operations: Dict[str, Operation] = {}
        self.operation_tasks: Dict[str, asyncio.Task] = {}
        self.websocket: WebSocket


class GraphQLTransportWSHandler(GraphQLWebsocketHandler):
    """Implementation of the (newer) graphql-transport-ws subprotocol from the graphql-ws library
    https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md
    """

    GQL_CONNECTION_INIT = "connection_init"  # Client -> Server
    GQL_CONNECTION_ACK = "connection_ack"  # Server -> Client
    GQL_PING = "ping"  # Client -> Server, Server -> Client
    GQL_PONG = "pong"  # Client -> Server, Server -> Client
    GQL_SUBSCRIBE = "subscribe"  # Client -> Server
    GQL_NEXT = "next"  # Server -> Client
    GQL_ERROR = "error"  # Server -> Client
    GQL_COMPLETE = "complete"  # Client -> Server, Server -> Client

    def __init__(
        self,
        *args,
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.connection_init_wait_timeout = connection_init_wait_timeout

    async def handle_connection_init_timeout(
        self, websocket: WebSocket, client_context: ClientContext
    ):
        delay = self.connection_init_wait_timeout.total_seconds()
        await asyncio.sleep(delay=delay)
        if client_context.connection_init_received:
            return
        # 4408: Connection initialisation timeout
        await websocket.close(code=4408)

    async def handle(self, scope: Scope, receive: Receive, send: Send):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        client_context = ClientContext()
        timeout_handler = self.handle_connection_init_timeout(websocket, client_context)
        client_context.connection_init_timeout_task = asyncio.create_task(
            timeout_handler
        )

        await websocket.accept("graphql-transport-ws")
        try:
            while WebSocketState.DISCONNECTED not in (
                websocket.client_state,
                websocket.application_state,
            ):
                message = await websocket.receive_json()
                await self.handle_websocket_message(websocket, message, client_context)
        except WebSocketDisconnect:
            pass
        finally:
            for operation_id in list(client_context.operations.keys()):
                await self.stop_websocket_operation(
                    websocket, operation_id, client_context
                )

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
        self, websocket: WebSocket, message: dict, client_context: ClientContext
    ):
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GraphQLTransportWSHandler.GQL_CONNECTION_INIT:
            await self.handle_websocket_connection_init_message(
                websocket, message, client_context
            )
        elif message_type == GraphQLTransportWSHandler.GQL_PING:
            await self.handle_websocket_ping_message(websocket, client_context)
        elif message_type == GraphQLTransportWSHandler.GQL_PONG:
            await self.handle_websocket_pong_message(client_context)
        elif message_type == GraphQLTransportWSHandler.GQL_COMPLETE:
            await self.handle_websocket_complete_message(
                websocket, operation_id, client_context
            )
        elif message_type == GraphQLTransportWSHandler.GQL_SUBSCRIBE:
            await self.handle_websocket_subscribe(
                websocket, message.get("payload"), operation_id, client_context
            )
        else:
            await self.handle_websocket_invalid_type(websocket)

    async def handle_websocket_connection_init_message(
        self, websocket: WebSocket, message: dict, client_context: ClientContext
    ):
        if client_context.connection_init_received:
            # 4429: Too many initialisation requests
            await websocket.close(code=4429)
            return

        client_context.connection_init_received = True

        try:
            if self.on_connect:
                result = self.on_connect(websocket, message.get("payload"))
                if result and isawaitable(result):
                    await result

            await websocket.send_json(
                {"type": GraphQLTransportWSHandler.GQL_CONNECTION_ACK}
            )
            client_context.connection_acknowledged = True
        except Exception as error:
            log_error(error, self.logger)
            await websocket.close()

    async def handle_websocket_ping_message(
        self,
        websocket: WebSocket,
        client_context: ClientContext,  # pylint: disable=unused-argument
    ):
        await websocket.send_json({"type": GraphQLTransportWSHandler.GQL_PONG})

    async def handle_websocket_pong_message(self, client_context: ClientContext):
        pass

    async def handle_websocket_complete_message(
        self, websocket: WebSocket, operation_id: str, client_context: ClientContext
    ):
        await self.stop_websocket_operation(websocket, operation_id, client_context)

    async def handle_websocket_subscribe(
        self,
        websocket: WebSocket,
        data: Any,
        operation_id: str,
        client_context: ClientContext,
    ):
        if not client_context.connection_acknowledged:
            await websocket.close(code=4401)
            return

        if operation_id in client_context.operations:
            await websocket.close(code=4409)
            return

        validate_data(data)

        try:
            graphql_document = parse_query(data.get("query"))
            operation_type = get_operation_type(
                graphql_document, data.get("operationName")
            )
        except GraphQLError as error:
            log_error(error, self.logger)
            await websocket.send_json(
                {
                    "type": GraphQLTransportWSHandler.GQL_ERROR,
                    "id": operation_id,
                    "payload": self.error_formatter(error, self.debug),
                }
            )
            return

        if operation_type == OperationType.SUBSCRIPTION:
            if self.schema is None:
                raise TypeError(
                    "schema is not set, call configure method to initialize it"
                )
            context_value = await self.get_context_for_request(websocket)
            success, results_producer = await subscribe(
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
        else:
            if self.http_handler is None:
                raise TypeError(
                    "http_handler is not set, call configure method to initialize it"
                )
            success, result = await self.http_handler.execute_graphql_query(
                websocket, data
            )

            async def get_results():
                yield result

            # if success then AsyncGenerator is expected, for error it will be List
            results_producer = get_results() if success else [result]

        if not success:
            results_producer = cast(List[dict], results_producer)
            await websocket.send_json(
                {
                    "type": GraphQLTransportWSHandler.GQL_ERROR,
                    "id": operation_id,
                    "payload": results_producer[0],
                }
            )
        else:
            results_producer = cast(
                AsyncGenerator[ExecutionResult, None], results_producer
            )
            client_context.operations[operation_id] = Operation(
                id=operation_id,
                name=data.get("operationName"),
                generator=results_producer,
            )

            if self.on_operation:
                try:
                    result = self.on_operation(
                        websocket, client_context.operations[operation_id]
                    )
                    if result and isawaitable(result):
                        await result
                except Exception as error:
                    if not isinstance(error, GraphQLError):
                        error = GraphQLError(str(error), original_error=error)
                    log_error(error, self.logger)

            # store Task in the operation_tasks list so that we can cancel such task
            # if client sends the "complete" message
            client_context.operation_tasks[operation_id] = asyncio.ensure_future(
                self.observe_async_results(
                    websocket, results_producer, operation_id, client_context
                )
            )

    async def handle_websocket_invalid_type(self, websocket: WebSocket):
        await websocket.close(code=4400)

    async def handle_on_complete(self, websocket: WebSocket, operation: Operation):
        if self.on_complete:
            try:
                result = self.on_complete(websocket, operation)
                if result and isawaitable(result):
                    await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

    async def stop_websocket_operation(
        self, websocket: WebSocket, operation_id: str, client_context: ClientContext
    ):
        if operation_id not in client_context.operations:
            return

        operation = client_context.operations.pop(operation_id)
        await self.handle_on_complete(websocket, operation)

        otask = client_context.operation_tasks.pop(operation_id)
        otask.cancel()
        with suppress(asyncio.CancelledError):
            await otask
        await operation.generator.aclose()

    async def observe_async_results(
        self,
        websocket: WebSocket,
        results_producer: AsyncGenerator,
        operation_id: str,
        client_context: ClientContext,
    ) -> None:
        try:
            async for result in results_producer:
                if not isinstance(result, dict):
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
                else:
                    payload = result

                await websocket.send_json(
                    {
                        "type": GraphQLTransportWSHandler.GQL_NEXT,
                        "id": operation_id,
                        "payload": payload,
                    }
                )
        except asyncio.CancelledError:  # pylint: disable=W0706
            # if asyncio Task is cancelled then CancelledError is thrown in the coroutine
            raise
        except Exception as error:
            if not isinstance(error, GraphQLError):
                error = GraphQLError(str(error), original_error=error)
            log_error(error, self.logger)
            payload = {"errors": [self.error_formatter(error, self.debug)]}

            await websocket.send_json(
                {
                    "type": GraphQLTransportWSHandler.GQL_NEXT,
                    "id": operation_id,
                    "payload": payload,
                }
            )

        operation = client_context.operations.pop(operation_id)
        del client_context.operation_tasks[operation_id]
        await self.handle_on_complete(websocket, operation)

        if WebSocketState.DISCONNECTED not in (
            websocket.client_state,
            websocket.application_state,
        ):
            await websocket.send_json(
                {"type": GraphQLTransportWSHandler.GQL_COMPLETE, "id": operation_id}
            )
