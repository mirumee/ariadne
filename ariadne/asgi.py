import asyncio
import json
from functools import partial
from typing import Any, AsyncGenerator, Dict, Optional, Tuple, cast

from graphql import (
    DocumentNode,
    ExecutionResult,
    GraphQLError,
    GraphQLSchema,
    format_error,
    graphql,
    parse,
    subscribe,
)
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from .constants import DATA_TYPE_JSON, PLAYGROUND_HTML
from .exceptions import HttpBadRequestError, HttpError

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
    def __init__(self, schema: GraphQLSchema, *, keepalive: float = None):
        self.keepalive = keepalive
        self.schema = schema

    def __call__(self, scope: Scope):
        assert scope["type"] in {"http", "websocket"}
        if scope["type"] == "http":
            return partial(self.handle_http, scope=scope)
        if scope["type"] == "websocket":
            return partial(self.handle_websocket, scope=scope)
        raise ValueError("Unknown scope type: %r" % (scope["type"],))

    async def context_for_request(self, request: Any) -> Any:
        return {"request": request}

    async def root_value_for_document(
        self, query: DocumentNode, variables: Optional[dict]
    ):
        return None

    async def handle_http(self, receive: Receive, send: Send, *, scope: Scope):
        request = Request(scope=scope, receive=receive)
        if request.method == "GET" and not request.query_params.get("query"):
            response = await self.render_playground(request)
        elif request.method in {"GET", "POST"}:
            response = await self.graphql_http_server(request)
        else:
            response = Response(status_code=400)
        await response(receive, send)

    async def handle_websocket(self, receive: Receive, send: Send, *, scope: Scope):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        await self.graphql_ws_server(websocket)

    def extract_data_from_request_query(
        self, query_params: dict
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        query = cast(str, query_params.get("query"))
        variables = query_params.get("variables")
        try:
            variables = cast(dict, json.loads(variables))
        except (TypeError, ValueError):
            variables = None
        operation_name = cast(str, query_params.get("operationName"))
        return query, variables, operation_name

    def extract_data_from_request_data(
        self, data: dict
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        if not isinstance(data, dict):
            raise GraphQLError("Valid request body should be a JSON object")

        query = cast(str, data.get("query"))
        variables = cast(dict, data.get("variables"))
        operation_name = cast(str, data.get("operationName"))
        return query, variables, operation_name

    async def extract_data_from_request(
        self, request: Request
    ) -> Tuple[str, Optional[dict], Optional[str]]:
        if request.method == "GET":
            return self.extract_data_from_request_query(request.query_params)
        if request.headers.get("Content-Type") != DATA_TYPE_JSON:
            raise HttpBadRequestError(
                "Posted content must be of type {}".format(DATA_TYPE_JSON)
            )

        data = await request.json()
        return self.extract_data_from_request_data(data)

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

    async def render_playground(self, request: Request) -> HTMLResponse:
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
            response = {"errors": [{"message": error.message}]}
            return JSONResponse(response)
        except HttpError as error:
            response = error.message or error.status
            return Response(response, status_code=400)
        else:
            response = {"data": result.data}
            if result.errors:
                response["errors"] = [format_error(e) for e in result.errors]
            return JSONResponse(response)

    async def observe_async_results(
        self, results: AsyncGenerator, operation_id: str, websocket: WebSocket
    ) -> None:
        async for result in results:
            payload = {}
            if result.data:
                payload["data"] = result.data
            if result.errors:
                payload["errors"] = [format_error(e) for e in result.errors]
            await self.send_json(
                websocket, {"type": GQL_DATA, "id": operation_id, "payload": payload}
            )
        await self.send_json(websocket, {"type": GQL_COMPLETE, "id": operation_id})

    async def keep_connection_alive(self, websocket: WebSocket):
        if not self.keepalive:
            return
        while True:
            if websocket.application_state == WebSocketState.DISCONNECTED:
                break
            await self.send_json(websocket, {"type": GQL_CONNECTION_KEEP_ALIVE})
            await asyncio.sleep(self.keepalive)

    async def receive_json(self, websocket: WebSocket) -> dict:
        message = await websocket.receive_text()
        return json.loads(message)

    async def send_json(self, websocket, message) -> None:
        message = json.dumps(message)
        await websocket.send_text(message)

    async def graphql_ws_server(self, websocket: WebSocket) -> None:
        subscriptions: Dict[str, AsyncGenerator] = {}
        await websocket.accept("graphql-ws")
        asyncio.ensure_future(self.keep_connection_alive(websocket))
        try:
            while True:
                message = await self.receive_json(websocket)
                operation_id = cast(str, message.get("id"))
                message_type = cast(str, message.get("type"))

                if message_type == GQL_CONNECTION_INIT:
                    await self.send_json(websocket, {"type": GQL_CONNECTION_ACK})
                elif message_type == GQL_CONNECTION_TERMINATE:
                    break
                elif message_type == GQL_START:
                    query, variables, operation_name = await self.extract_data_from_websocket(
                        message
                    )
                    document = parse(query)
                    results = await subscribe(
                        self.schema,
                        document,
                        root_value=await self.root_value_for_document(
                            document, variables
                        ),
                        context_value=await self.context_for_request(message),
                        variable_values=variables,
                        operation_name=operation_name,
                    )
                    if isinstance(results, ExecutionResult):
                        payload = {"message": format_error(results.errors[0])}
                        await self.send_json(
                            websocket,
                            {"type": GQL_ERROR, "id": operation_id, "payload": payload},
                        )
                    else:
                        subscriptions[operation_id] = results
                        asyncio.ensure_future(
                            self.observe_async_results(results, operation_id, websocket)
                        )
                elif message_type == GQL_STOP:
                    if operation_id in subscriptions:
                        await subscriptions[operation_id].aclose()
                        del subscriptions[operation_id]
        except WebSocketDisconnect:
            for operation_id in subscriptions:
                await subscriptions[operation_id].aclose()
                del subscriptions[operation_id]
