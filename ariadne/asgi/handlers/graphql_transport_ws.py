import asyncio
from contextlib import suppress
from datetime import timedelta
from inspect import isawaitable
from typing import Any, AsyncGenerator, Dict, List, Optional, cast

from graphql import GraphQLError, GraphQLSchema
from graphql.language import OperationType
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from .base import GraphQLWebsocketHandler
from .http import GraphQLHTTPHandler
from ...format_error import format_error
from ...graphql import subscribe, parse_query, validate_data
from ...logger import log_error
from ...types import (
    ContextValue,
    ErrorFormatter,
    ExecutionResult,
    OnComplete,
    OnConnect,
    OnDisconnect,
    OnOperation,
    Operation,
    RootValue,
    ValidationRules,
)
from ...utils import get_operation_type


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
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        on_connect: Optional[OnConnect] = None,
        on_disconnect: Optional[OnDisconnect] = None,
        on_operation: Optional[OnOperation] = None,
        on_complete: Optional[OnComplete] = None,
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        http_handler: Optional[GraphQLHTTPHandler] = None,
    ):
        super().__init__()
        self.context_value = context_value
        self.root_value = root_value
        self.validation_rules = validation_rules
        self.debug = debug
        self.introspection = introspection
        self.logger = logger
        self.error_formatter = error_formatter
        self.schema = schema
        self.http_handler = http_handler
        self.websocket: WebSocket
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_operation = on_operation
        self.on_complete = on_complete

        self.operations: Dict[str, Operation] = {}
        self.operation_tasks: Dict[str, asyncio.Task] = {}
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.connection_init_timeout_task: Optional[asyncio.Task] = None
        self.connection_init_received: bool = False
        self.connection_acknowledged: bool = False

    async def handle_connection_init_timeout(self, websocket: WebSocket):
        delay = self.connection_init_wait_timeout.total_seconds()
        await asyncio.sleep(delay=delay)
        if self.connection_init_received:
            return
        # 4408: Connection initialisation timeout
        await websocket.close(code=4408)

    async def handle(self, scope: Scope, receive: Receive, send: Send):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        timeout_handler = self.handle_connection_init_timeout(websocket)
        self.connection_init_timeout_task = asyncio.create_task(timeout_handler)

        await websocket.accept("graphql-transport-ws")
        try:
            while WebSocketState.DISCONNECTED not in (
                websocket.client_state,
                websocket.application_state,
            ):
                message = await websocket.receive_json()
                await self.handle_websocket_message(websocket, message)
        except WebSocketDisconnect:
            pass
        finally:
            for operation_id in list(self.operations.keys()):
                await self.stop_websocket_operation(websocket, operation_id)

            try:
                if self.on_disconnect:
                    result = self.on_disconnect(websocket)
                    if result and isawaitable(result):
                        await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

    async def handle_websocket_message(self, websocket: WebSocket, message: dict):
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GraphQLTransportWSHandler.GQL_CONNECTION_INIT:
            await self.handle_websocket_connection_init_message(websocket, message)
        elif message_type == GraphQLTransportWSHandler.GQL_PING:
            await self.handle_websocket_ping_message(websocket)
        elif message_type == GraphQLTransportWSHandler.GQL_PONG:
            await self.handle_websocket_pong_message()
        elif message_type == GraphQLTransportWSHandler.GQL_COMPLETE:
            await self.handle_websocket_complete_message(websocket, operation_id)
        elif message_type == GraphQLTransportWSHandler.GQL_SUBSCRIBE:
            await self.handle_websocket_subscribe(
                websocket, message.get("payload"), operation_id
            )
        else:
            await self.handle_websocket_invalid_type(websocket)

    async def handle_websocket_connection_init_message(
        self, websocket: WebSocket, message: dict
    ):
        if self.connection_init_received:
            # 4429: Too many initialisation requests
            await websocket.close(code=4429)
            return

        self.connection_init_received = True

        try:
            if self.on_connect:
                result = self.on_connect(websocket, message.get("payload"))
                if result and isawaitable(result):
                    await result

            await websocket.send_json(
                {"type": GraphQLTransportWSHandler.GQL_CONNECTION_ACK}
            )
            self.connection_acknowledged = True
        except Exception as error:
            log_error(error, self.logger)
            await websocket.close()

    async def handle_websocket_ping_message(self, websocket: WebSocket):
        await websocket.send_json({"type": GraphQLTransportWSHandler.GQL_PONG})

    async def handle_websocket_pong_message(self):
        pass

    async def handle_websocket_complete_message(
        self, websocket: WebSocket, operation_id: str
    ):
        await self.stop_websocket_operation(websocket, operation_id)

    async def handle_websocket_subscribe(
        self, websocket: WebSocket, data: Any, operation_id: str
    ):
        if not self.connection_acknowledged:
            await websocket.close(code=4401)
            return

        if operation_id in self.operations:
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
            # single result
            if not self.http_handler:
                await websocket.close(code=4406)
                return

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
            self.operations[operation_id] = Operation(
                id=operation_id,
                name=data.get("operationName"),
                generator=results_producer,
            )

            if self.on_operation:
                try:
                    result = self.on_operation(websocket, self.operations[operation_id])
                    if result and isawaitable(result):
                        await result
                except Exception as error:
                    if not isinstance(error, GraphQLError):
                        error = GraphQLError(str(error), original_error=error)
                    log_error(error, self.logger)

            # store Task in the operation_tasks list so that we can cancel such task
            # if client sends the "complete" message
            self.operation_tasks[operation_id] = asyncio.ensure_future(
                self.observe_async_results(websocket, results_producer, operation_id)
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

    async def stop_websocket_operation(self, websocket: WebSocket, operation_id: str):
        if operation_id not in self.operations:
            return

        operation = self.operations.pop(operation_id)
        await self.handle_on_complete(websocket, operation)

        otask = self.operation_tasks.pop(operation_id)
        otask.cancel()
        with suppress(asyncio.CancelledError):
            await otask
        await operation.generator.aclose()

    async def observe_async_results(
        self, websocket: WebSocket, results_producer: AsyncGenerator, operation_id: str
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

        operation = self.operations.pop(operation_id)
        del self.operation_tasks[operation_id]
        await self.handle_on_complete(websocket, operation)

        if WebSocketState.DISCONNECTED not in (
            websocket.client_state,
            websocket.application_state,
        ):
            await websocket.send_json(
                {"type": GraphQLTransportWSHandler.GQL_COMPLETE, "id": operation_id}
            )
