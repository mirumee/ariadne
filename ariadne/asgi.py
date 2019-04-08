import asyncio
from functools import partial
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, cast

from graphql import GraphQLError, GraphQLSchema
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

from .constants import DATA_TYPE_JSON, PLAYGROUND_HTML
from .exceptions import HttpBadRequestError, HttpError
from .format_errors import format_error
from .graphql import graphql, subscribe
from .types import ErrorFormatter

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


class GraphQL:
    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        debug: bool = False,
        error_formatter: ErrorFormatter = format_error,
        keepalive: float = None,
    ):
        self.debug = debug
        self.error_formatter = error_formatter
        self.keepalive = keepalive
        self.schema = schema

    def __call__(self, scope: Scope):
        if scope["type"] == "http":
            return partial(self.handle_http, scope=scope)
        if scope["type"] == "websocket":
            return partial(self.handle_websocket, scope=scope)
        raise ValueError("Unknown scope type: %r" % (scope["type"],))

    async def context_for_request(  # pylint: disable=unused-argument
        self, request: Any, data: Any
    ) -> Any:
        return {"request": request}

    async def root_value_for_document(  # pylint: disable=unused-argument
        self, request: Any, data: Any
    ):
        return None

    async def handle_http(self, receive: Receive, send: Send, *, scope: Scope):
        request = Request(scope=scope, receive=receive)
        if request.method == "GET":
            response = await self.render_playground(request)
        elif request.method == "POST":
            response = await self.graphql_http_server(request)
        else:
            response = Response(status_code=405)
        await response(receive, send)

    async def handle_websocket(self, receive: Receive, send: Send, *, scope: Scope):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        await self.websocket_server(websocket)

    async def extract_data_from_request(
        self, request: Request
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        if request.headers.get("Content-Type") != DATA_TYPE_JSON:
            raise HttpBadRequestError(
                "Posted content must be of type {}".format(DATA_TYPE_JSON)
            )
        try:
            return await request.json()
        except ValueError:
            raise HttpBadRequestError("Request body is not a valid JSON")

    async def render_playground(  # pylint: disable=unused-argument
        self, request: Request
    ) -> HTMLResponse:
        return HTMLResponse(PLAYGROUND_HTML)

    async def graphql_http_server(self, request: Request) -> Response:
        try:
            data = await self.extract_data_from_request(request)
        except HttpError as error:
            return Response(error.message or error.status, status_code=400)

        context_value = await self.context_for_request(request, data)
        root_value = await self.root_value_for_document(request, data)
        success, response = await graphql(
            self.schema,
            data,
            root_value=root_value,
            context_value=context_value,
            debug=self.debug,
            error_formatter=self.error_formatter,
        )
        status_code = 200 if success else 400
        return JSONResponse(response, status_code=status_code)

    async def websocket_server(self, websocket: WebSocket) -> None:
        subscriptions: Dict[str, AsyncGenerator] = {}
        await websocket.accept("graphql-ws")
        try:
            while websocket.application_state != WebSocketState.DISCONNECTED:
                message = await websocket.receive_json()
                await self.handle_websocket_message(message, websocket, subscriptions)
        except WebSocketDisconnect:
            pass
        finally:
            for operation_id in subscriptions:
                await subscriptions[operation_id].aclose()

    async def handle_websocket_message(  # pylint: disable=too-complex
        self,
        message: dict,
        websocket: WebSocket,
        subscriptions: Dict[str, AsyncGenerator],
    ):
        operation_id = cast(str, message.get("id"))
        message_type = cast(str, message.get("type"))

        if message_type == GQL_CONNECTION_INIT:
            await websocket.send_json({"type": GQL_CONNECTION_ACK})
            asyncio.ensure_future(self.keep_websocket_alive(websocket))
        elif message_type == GQL_CONNECTION_TERMINATE:
            await websocket.close()
        elif message_type == GQL_START:
            await self.start_websocket_subscription(
                message.get("payload"), operation_id, websocket, subscriptions
            )
        elif message_type == GQL_STOP:
            if operation_id in subscriptions:
                await subscriptions[operation_id].aclose()
                del subscriptions[operation_id]

    async def keep_websocket_alive(self, websocket: WebSocket):
        if not self.keepalive:
            return
        while websocket.application_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.send_json({"type": GQL_CONNECTION_KEEP_ALIVE})
            except WebSocketDisconnect:
                return
            await asyncio.sleep(self.keepalive)

    async def start_websocket_subscription(
        self,
        data: Any,
        operation_id: str,
        websocket: WebSocket,
        subscriptions: Dict[str, AsyncGenerator],
    ):
        context_value = await self.context_for_request(websocket, data)
        root_value = await self.root_value_for_document(websocket, data)
        success, results = await subscribe(
            self.schema,
            data,
            root_value=root_value,
            context_value=context_value,
            debug=self.debug,
            error_formatter=self.error_formatter,
        )
        if not success:
            results = cast(List[GraphQLError], results)
            await websocket.send_json(
                {"type": GQL_ERROR, "id": operation_id, "payload": results[0]}
            )
        else:
            results = cast(AsyncGenerator, results)
            subscriptions[operation_id] = results
            asyncio.ensure_future(
                self.observe_async_results(results, operation_id, websocket)
            )

    async def extract_data_from_websocket(
        self, message: dict
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        payload = cast(dict, message.get("payload"))
        if not isinstance(payload, dict):
            raise GraphQLError("Payload must be an object")

        query = cast(str, payload.get("query"))
        variables = cast(dict, payload.get("variables"))
        operation_name = cast(str, payload.get("operationName"))

        return query, variables, operation_name

    async def observe_async_results(
        self, results: AsyncGenerator, operation_id: str, websocket: WebSocket
    ) -> None:
        async for result in results:
            payload = {}
            if result.data:
                payload["data"] = result.data
            if result.errors:
                payload["errors"] = [
                    format_error(error, debug=self.debug) for error in result.errors
                ]
            await websocket.send_json(
                {"type": GQL_DATA, "id": operation_id, "payload": payload}
            )
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.send_json({"type": GQL_COMPLETE, "id": operation_id})
