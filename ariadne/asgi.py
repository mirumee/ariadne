import asyncio
from functools import partial
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, cast

from graphql import (
    DocumentNode,
    ExecutionResult,
    GraphQLError,
    GraphQLSchema,
    graphql,
    parse,
    subscribe,
)
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

from .constants import DATA_TYPE_JSON, PLAYGROUND_HTML
from .exceptions import HttpBadRequestError, HttpError
from .format_errors import format_errors, format_error
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
        keepalive: float = None
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

    async def context_for_request(self, request: Any) -> Any:
        return {"request": request}

    async def root_value_for_document(  # pylint: disable=unused-argument
        self, query: DocumentNode, variables: Optional[dict]
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

    def extract_data_from_request_data(
        self, data: dict
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        if not isinstance(data, dict):
            raise GraphQLError("Valid request body should be a JSON object")

        query = cast(str, data.get("query"))
        if not query or not isinstance(query, str):
            raise GraphQLError("The query must be a string.")
        variables = cast(dict, data.get("variables"))
        if variables and not isinstance(variables, dict):
            raise GraphQLError("Query variables must be a null or an object.")
        operation_name = cast(str, data.get("operationName"))
        if operation_name is not None and not isinstance(operation_name, str):
            raise GraphQLError('"%s" is not a valid operation name.' % operation_name)
        return query, variables, operation_name

    async def extract_data_from_request(
        self, request: Request
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        if request.headers.get("Content-Type") != DATA_TYPE_JSON:
            raise HttpBadRequestError(
                "Posted content must be of type {}".format(DATA_TYPE_JSON)
            )

        try:
            data = await request.json()
        except ValueError:
            raise HttpBadRequestError("Request body is not a valid JSON")
        return self.extract_data_from_request_data(data)

    async def render_playground(  # pylint: disable=unused-argument
        self, request: Request
    ) -> HTMLResponse:
        return HTMLResponse(PLAYGROUND_HTML)

    async def graphql_http_server(self, request: Request) -> Response:
        try:
            query, variables, operation_name = await self.extract_data_from_request(
                request
            )
            document = parse(query)
            result = await graphql(
                self.schema,
                query,
                root_value=await self.root_value_for_document(document, variables),
                context_value=await self.context_for_request(request),
                variable_values=variables,
                operation_name=operation_name,
            )
        except GraphQLError as error:
            return JSONResponse(
                {"errors": [{"message": error.message}]}, status_code=400
            )
        except HttpError as error:
            return Response(error.message or error.status, status_code=400)
        else:
            response = {"data": result.data}
            if result.errors:
                response["errors"] = format_errors(
                    result, self.error_formatter, self.debug
                )
            return JSONResponse(response)

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
                message, operation_id, websocket, subscriptions
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
        message: dict,
        operation_id: str,
        websocket: WebSocket,
        subscriptions: Dict[str, AsyncGenerator],
    ):
        query, variables, operation_name = await self.extract_data_from_websocket(
            message
        )
        document = parse(query)
        results = await subscribe(
            self.schema,
            document,
            root_value=await self.root_value_for_document(document, variables),
            context_value=await self.context_for_request(message),
            variable_values=variables,
            operation_name=operation_name,
        )
        if isinstance(results, ExecutionResult):
            payload = {
                "message": format_errors(results, self.error_formatter, self.debug)[0]
            }
            await websocket.send_json(
                {"type": GQL_ERROR, "id": operation_id, "payload": payload}
            )
        else:
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
                payload["errors"] = format_errors(
                    result, self.error_formatter, self.debug
                )
            await websocket.send_json(
                {"type": GQL_DATA, "id": operation_id, "payload": payload}
            )
        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.send_json({"type": GQL_COMPLETE, "id": operation_id})
