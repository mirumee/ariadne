import asyncio
import json
from dataclasses import dataclass
from inspect import isawaitable
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    cast,
)

from graphql import GraphQLError, GraphQLSchema
from graphql.execution import Middleware, MiddlewareManager
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

from .constants import (
    DATA_TYPE_JSON,
    DATA_TYPE_MULTIPART,
    PLAYGROUND_HTML,
)
from .exceptions import HttpBadRequestError, HttpError
from .file_uploads import combine_multipart_data
from .format_error import format_error
from .graphql import graphql, subscribe
from .logger import log_error
from .types import (
    ContextValue,
    ErrorFormatter,
    ExtensionList,
    RootValue,
    ValidationRules,
)

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


class WebSocketConnectionError(Exception):
    """Special error class enabling custom error reporting for on_connect"""

    def __init__(self, payload: Union[dict, str] = None):
        if isinstance(payload, dict):
            self.payload = payload
        else:
            self.payload = {"message": str(payload)}


Extensions = Union[
    Callable[[Any, Optional[ContextValue]], ExtensionList], ExtensionList
]
MiddlewareList = Optional[List[Middleware]]
Middlewares = Union[
    Callable[[Any, Optional[ContextValue]], MiddlewareList], MiddlewareList
]


@dataclass
class Operation:
    id: str
    name: Optional[str]
    generator: AsyncGenerator


OnConnect = Callable[[WebSocket, Any], Any]
OnDisconnect = Callable[[WebSocket], Any]
OnOperation = Callable[[WebSocket, Operation], Any]
OnComplete = Callable[[WebSocket, Operation], Any]


class GraphQL:
    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        on_connect: Optional[OnConnect] = None,
        on_disconnect: Optional[OnDisconnect] = None,
        on_operation: Optional[OnOperation] = None,
        on_complete: Optional[OnComplete] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
        keepalive: float = None,
    ):
        self.context_value = context_value
        self.root_value = root_value
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_operation = on_operation
        self.on_complete = on_complete
        self.validation_rules = validation_rules
        self.debug = debug
        self.introspection = introspection
        self.logger = logger
        self.error_formatter = error_formatter
        self.extensions = extensions
        self.middleware = middleware
        self.keepalive = keepalive
        self.schema = schema

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.handle_http(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope=scope, receive=receive, send=send)
        else:
            raise ValueError("Unknown scope type: %r" % (scope["type"],))

    async def get_context_for_request(
        self,
        request: Any,
    ) -> Any:
        if callable(self.context_value):
            context = self.context_value(request)
            if isawaitable(context):
                context = await context
            return context

        return self.context_value or {"request": request}

    async def get_extensions_for_request(
        self, request: Any, context: Optional[ContextValue]
    ) -> ExtensionList:
        if callable(self.extensions):
            extensions = self.extensions(request, context)
            if isawaitable(extensions):
                extensions = await extensions  # type: ignore
            return extensions
        return self.extensions

    async def get_middleware_for_request(
        self, request: Any, context: Optional[ContextValue]
    ) -> Optional[MiddlewareManager]:
        middleware = self.middleware
        if callable(middleware):
            middleware = middleware(request, context)
            if isawaitable(middleware):
                middleware = await middleware  # type: ignore
        if middleware:
            middleware = cast(list, middleware)
            return MiddlewareManager(*middleware)
        return None

    async def handle_http(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope=scope, receive=receive)
        if request.method == "GET" and self.introspection:
            # only render playground when introspection is enabled
            response = await self.render_playground(request)
        elif request.method == "POST":
            response = await self.graphql_http_server(request)
        else:
            response = self.handle_not_allowed_method(request)
        await response(scope, receive, send)

    async def handle_websocket(self, scope: Scope, receive: Receive, send: Send):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        await self.websocket_server(websocket)

    async def render_playground(  # pylint: disable=unused-argument
        self, request: Request
    ) -> Response:
        return HTMLResponse(PLAYGROUND_HTML)

    async def graphql_http_server(self, request: Request) -> Response:
        try:
            data = await self.extract_data_from_request(request)
        except HttpError as error:
            return PlainTextResponse(error.message or error.status, status_code=400)

        context_value = await self.get_context_for_request(request)
        extensions = await self.get_extensions_for_request(request, context_value)
        middleware = await self.get_middleware_for_request(request, context_value)

        success, result = await graphql(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            validation_rules=self.validation_rules,
            debug=self.debug,
            introspection=self.introspection,
            logger=self.logger,
            error_formatter=self.error_formatter,
            extensions=extensions,
            middleware=middleware,
        )
        return await self.create_json_response(request, result, success)

    async def create_json_response(
        self,
        request: Request,  # pylint: disable=unused-argument
        result: dict,
        success: bool,
    ) -> Response:
        status_code = 200 if success else 400
        return JSONResponse(result, status_code=status_code)

    async def extract_data_from_request(self, request: Request):
        content_type = request.headers.get("Content-Type", "")
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            return await self.extract_data_from_json_request(request)
        if content_type == DATA_TYPE_MULTIPART:
            return await self.extract_data_from_multipart_request(request)

        raise HttpBadRequestError(
            "Posted content must be of type {} or {}".format(
                DATA_TYPE_JSON, DATA_TYPE_MULTIPART
            )
        )

    async def extract_data_from_json_request(self, request: Request):
        try:
            return await request.json()
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError("Request body is not a valid JSON") from ex

    async def extract_data_from_multipart_request(self, request: Request):
        try:
            request_body = await request.form()
        except ValueError as ex:
            raise HttpBadRequestError(
                "Request body is not a valid multipart/form-data"
            ) from ex

        try:
            operations = json.loads(request_body.get("operations"))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'operations' multipart field is not a valid JSON"
            ) from ex
        try:
            files_map = json.loads(request_body.get("map"))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'map' multipart field is not a valid JSON"
            ) from ex

        request_files = {
            key: value
            for key, value in request_body.items()
            if isinstance(value, UploadFile)
        }

        return combine_multipart_data(operations, files_map, request_files)

    def handle_not_allowed_method(self, request: Request):
        allowed_methods = ["OPTIONS", "POST"]
        if self.introspection:
            allowed_methods.append("GET")
        allow_header = {"Allow": ", ".join(allowed_methods)}

        if request.method == "OPTIONS":
            return Response(headers=allow_header)

        return Response(status_code=405, headers=allow_header)

    async def websocket_server(self, websocket: WebSocket) -> None:
        operations: Dict[str, Operation] = {}
        await websocket.accept("graphql-ws")
        try:
            while WebSocketState.DISCONNECTED not in (
                websocket.client_state,
                websocket.application_state,
            ):
                message = await websocket.receive_json()
                await self.handle_websocket_message(message, websocket, operations)
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
        message: dict,
        websocket: WebSocket,
        operations: Dict[str, Operation],
    ):
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GQL_CONNECTION_INIT:
            await self.handle_websocket_connection_init_message(
                message,
                websocket,
            )
        elif message_type == GQL_CONNECTION_TERMINATE:
            await self.handle_websocket_connection_terminate_message(
                websocket,
            )
        elif message_type == GQL_START:
            await self.start_websocket_operation(
                message.get("payload"), operation_id, websocket, operations
            )
        elif message_type == GQL_STOP:
            if operation_id in operations:
                await self.stop_websocket_operation(websocket, operations[operation_id])
                del operations[operation_id]

    async def handle_websocket_connection_init_message(
        self,
        message: dict,
        websocket: WebSocket,
    ):
        try:
            if self.on_connect:
                result = self.on_connect(websocket, message.get("payload"))
                if result and isawaitable(result):
                    await result

            await websocket.send_json({"type": GQL_CONNECTION_ACK})
            asyncio.ensure_future(self.keep_websocket_alive(websocket))
        except Exception as error:
            log_error(error, self.logger)

            if isinstance(error, WebSocketConnectionError):
                payload = error.payload  # pylint: disable=no-member
            else:
                payload = {"message": "Unexpected error has occurred."}

            await websocket.send_json(
                {"type": GQL_CONNECTION_ERROR, "payload": payload}
            )
            await websocket.close()

    async def handle_websocket_connection_terminate_message(
        self,
        websocket: WebSocket,
    ):
        await websocket.close()

    async def keep_websocket_alive(self, websocket: WebSocket):
        if not self.keepalive:
            return
        while websocket.application_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.send_json({"type": GQL_CONNECTION_KEEP_ALIVE})
            except WebSocketDisconnect:
                return
            await asyncio.sleep(self.keepalive)

    async def start_websocket_operation(
        self,
        data: Any,
        operation_id: str,
        websocket: WebSocket,
        operations: Dict[str, Operation],
    ):
        context_value = await self.get_context_for_request(websocket)

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
            await websocket.send_json(
                {"type": GQL_ERROR, "id": operation_id, "payload": results[0]}
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
                self.observe_async_results(results, operation_id, websocket)
            )

    async def stop_websocket_operation(
        self, websocket: WebSocket, operation: Operation
    ):
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
        self, results: AsyncGenerator, operation_id: str, websocket: WebSocket
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
                await websocket.send_json(
                    {"type": GQL_DATA, "id": operation_id, "payload": payload}
                )
        except Exception as error:
            if not isinstance(error, GraphQLError):
                error = GraphQLError(str(error), original_error=error)
            log_error(error, self.logger)
            payload = {"errors": [self.error_formatter(error, self.debug)]}
            await websocket.send_json(
                {"type": GQL_DATA, "id": operation_id, "payload": payload}
            )

        if WebSocketState.DISCONNECTED not in (
            websocket.client_state,
            websocket.application_state,
        ):
            await websocket.send_json({"type": GQL_COMPLETE, "id": operation_id})
