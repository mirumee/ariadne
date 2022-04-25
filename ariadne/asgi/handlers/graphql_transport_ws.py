import asyncio
from datetime import timedelta
from typing import Dict, cast, Optional, Any, AsyncGenerator, List
from inspect import isawaitable
from contextlib import suppress

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
    ContextValue,
    ErrorFormatter,
    RootValue,
    ValidationRules,
    Extensions,
    Middlewares,
    ExecutionResult,
)
from .graphql_base import GraphQLWebsocketBase


class GraphQLTransportWS(GraphQLWebsocketBase):
    """Implementation of the (newer) graphql-transport-ws subprotocol from the graphql-ws library
    https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md
    """

    PROTOCOL = "graphql-transport-ws"

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
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
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

        # GraphQLTransportWS specific attributes
        self.operations: Dict[str, Operation] = {}
        self.operation_tasks: Dict[str, asyncio.Task] = {}
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.connection_init_timeout_task: Optional[asyncio.Task] = None
        self.connection_init_received: bool = False
        self.connection_acknowledged: bool = False

    async def handle_connection_init_timeout(self):
        delay = self.connection_init_wait_timeout.total_seconds()
        await asyncio.sleep(delay=delay)
        if self.connection_init_received:
            return
        # 4408: Connection initialisation timeout
        await self.websocket.close(code=4408)

    async def handle_websocket(self):
        timeout_handler = self.handle_connection_init_timeout()
        self.connection_init_timeout_task = asyncio.create_task(timeout_handler)

        await self.websocket.accept("graphql-transport-ws")
        try:
            while WebSocketState.DISCONNECTED not in (
                self.websocket.client_state,
                self.websocket.application_state,
            ):
                message = await self.websocket.receive_json()
                await self.handle_websocket_message(message)
        except WebSocketDisconnect:
            pass
        finally:
            for operation_id in list(self.operations.keys()):
                await self.stop_websocket_operation(operation_id)

            try:
                if self.on_disconnect:
                    result = self.on_disconnect(self.websocket)
                    if result and isawaitable(result):
                        await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

    async def handle_websocket_message(self, message: dict):
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GraphQLTransportWS.GQL_CONNECTION_INIT:
            await self.handle_websocket_connection_init_message(message)
        elif message_type == GraphQLTransportWS.GQL_PING:
            await self.handle_websocket_ping_message()
        elif message_type == GraphQLTransportWS.GQL_PONG:
            await self.handle_websocket_pong_message()
        elif message_type == GraphQLTransportWS.GQL_COMPLETE:
            await self.handle_websocket_complete_message(operation_id)
        elif message_type == GraphQLTransportWS.GQL_SUBSCRIBE:
            await self.handle_websocket_subscribe(message.get("payload"), operation_id)
        else:
            await self.handle_websocket_invalid_type()

    async def handle_websocket_connection_init_message(self, message: dict):
        if self.connection_init_received:
            # 4429: Too many initialisation requests
            await self.websocket.close(code=4429)
            return

        self.connection_init_received = True

        try:
            if self.on_connect:
                result = self.on_connect(self.websocket, message.get("payload"))
                if result and isawaitable(result):
                    await result

            await self.websocket.send_json(
                {"type": GraphQLTransportWS.GQL_CONNECTION_ACK}
            )
            self.connection_acknowledged = True
        except Exception as error:
            log_error(error, self.logger)
            await self.websocket.close()

    async def handle_websocket_ping_message(self):
        try:
            await self.websocket.send_json({"type": GraphQLTransportWS.GQL_PONG})
        except WebSocketDisconnect:
            return

    async def handle_websocket_pong_message(self):
        pass

    async def handle_websocket_complete_message(self, operation_id: str):
        await self.stop_websocket_operation(operation_id)

    async def handle_websocket_subscribe(self, data: Any, operation_id: str):
        if not self.connection_acknowledged:
            await self.websocket.close(code=4401)
            return

        if operation_id in self.operations:
            await self.websocket.close(code=4409)
            return

        validate_data(data)

        try:
            graphql_document = parse_query(data.get("query"))
            operation_type = get_operation_type(
                graphql_document, data.get("operationName")
            )
        except GraphQLError as error:
            log_error(error, self.logger)
            await self.websocket.send_json(
                {
                    "type": GraphQLTransportWS.GQL_ERROR,
                    "id": operation_id,
                    "payload": self.error_formatter(error, self.debug),
                }
            )
            return

        if operation_type == OperationType.SUBSCRIPTION:
            context_value = await self.get_context_for_request(self.websocket)
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
            success, result = await self.execute_graphql_query(self.websocket, data)

            async def get_results():
                yield result

            # if success then AsyncGenerator is expected, for error it will be List
            results_producer = get_results() if success else [result]

        if not success:
            results_producer = cast(List[dict], results_producer)
            await self.websocket.send_json(
                {
                    "type": GraphQLTransportWS.GQL_ERROR,
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
                    result = self.on_operation(
                        self.websocket, self.operations[operation_id]
                    )
                    if result and isawaitable(result):
                        await result
                except Exception as error:
                    if not isinstance(error, GraphQLError):
                        error = GraphQLError(str(error), original_error=error)
                    log_error(error, self.logger)

            # store Task in the operation_tasks list so that we can cancel such task
            # if client sends the "complete" message
            self.operation_tasks[operation_id] = asyncio.ensure_future(
                self.observe_async_results(results_producer, operation_id)
            )

    async def handle_websocket_invalid_type(self):
        await self.websocket.close(code=4400)

    async def handle_on_complete(self, operation: Operation):
        if self.on_complete:
            try:
                result = self.on_complete(self.websocket, operation)
                if result and isawaitable(result):
                    await result
            except Exception as error:
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(str(error), original_error=error)
                log_error(error, self.logger)

    async def stop_websocket_operation(self, operation_id: str):
        if operation_id not in self.operations:
            return

        operation = self.operations.pop(operation_id)
        await self.handle_on_complete(operation)

        otask = self.operation_tasks.pop(operation_id)
        otask.cancel()
        with suppress(asyncio.CancelledError):
            await otask
        await operation.generator.aclose()

    async def observe_async_results(
        self, results_producer: AsyncGenerator, operation_id: str
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

                await self.websocket.send_json(
                    {
                        "type": GraphQLTransportWS.GQL_NEXT,
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

            await self.websocket.send_json(
                {
                    "type": GraphQLTransportWS.GQL_NEXT,
                    "id": operation_id,
                    "payload": payload,
                }
            )

        operation = self.operations.pop(operation_id)
        del self.operation_tasks[operation_id]
        await self.handle_on_complete(operation)

        if WebSocketState.DISCONNECTED not in (
            self.websocket.client_state,
            self.websocket.application_state,
        ):
            await self.websocket.send_json(
                {"type": GraphQLTransportWS.GQL_COMPLETE, "id": operation_id}
            )
