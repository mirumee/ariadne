import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, cast

from graphql import GraphQLError, GraphQLSchema
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket, WebSocketState, WebSocketDisconnect

from .constants import DATA_TYPE_JSON, PLAYGROUND_HTML, DATA_TYPE_MULTIPART
from .exceptions import HttpBadRequestError, HttpError
from .format_error import format_error
from .graphql import graphql, subscribe
from .logger import log_error
from .types import ContextValue, ErrorFormatter, RootValue

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

#### TMP

def place_files_in_operations(operations, files_map, files):
    """Replaces None placeholders in operations with file objects in the files
    dictionary, by following the files_map logic as specified within the 'map'
    request parameter in the multipart request spec"""
    path_to_key_iter = (
        (value.split('.'), key)
        for (key, values) in files_map.items()
        for value in values
    )
    # Since add_files_to_operations returns a new dict/list, first define
    # output to be operations itself
    output = operations
    for path, key in path_to_key_iter:
        file_obj = files[key]
        output = add_file_to_operations(output, file_obj, path)
    return output


def add_file_to_operations(operations, file_obj, path):
    """Handles the recursive algorithm for adding a file to the operations
    object"""
    if not path:
        if operations is not None:
            raise ValueError('Path in map does not lead to a null value')
        return file_obj
    if isinstance(operations, dict):
        key = path[0]
        sub_dict = add_file_to_operations(operations[key], file_obj, path[1:])
        return new_merged_dict(operations, {key: sub_dict})
    if isinstance(operations, list):
        index = int(path[0])
        sub_item = add_file_to_operations(
            operations[index],
            file_obj,
            path[1:],
        )
        return new_list_with_replaced_item(operations, index, sub_item)
    raise TypeError('Operations must be a dict or a list of dicts')


def new_merged_dict(*dicts):
    """Merges dictionaries into a new dictionary. Necessary for python2 and
    python34 since neither have PEP448 implemented."""
    # Necessary for python2 support
    output = {}
    for d in dicts:
        output.update(d)
    return output


def new_list_with_replaced_item(input_list, index, new_value):
    """Creates new list with replaced item at specified index"""
    output = [i for i in input_list]
    output[index] = new_value
    return output


####






class GraphQL:
    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        debug: bool = False,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        keepalive: float = None,
    ):
        self.context_value = context_value
        self.root_value = root_value
        self.debug = debug
        self.logger = logger
        self.error_formatter = error_formatter
        self.keepalive = keepalive
        self.schema = schema

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.handle_http(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.handle_websocket(scope=scope, receive=receive, send=send)
        else:
            raise ValueError("Unknown scope type: %r" % (scope["type"],))

    async def get_context_for_request(self, request: Any) -> Any:
        if callable(self.context_value):
            return self.context_value(request)
        return self.context_value or {"request": request}

    async def handle_http(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope=scope, receive=receive)
        if request.method == "GET":
            response = await self.render_playground(request)
        elif request.method == "POST":
            response = await self.graphql_http_server(request)
        else:
            response = Response(status_code=405)
        await response(scope, receive, send)

    async def handle_websocket(self, scope: Scope, receive: Receive, send: Send):
        websocket = WebSocket(scope=scope, receive=receive, send=send)
        await self.websocket_server(websocket)

    async def extract_data_from_request(
        self, request: Request
    ) -> Tuple[str, Optional[dict], Optional[str]]:

        content_type = request.headers.get("Content-Type")
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            try:
                return await request.json()
            except ValueError:
                raise HttpBadRequestError("Request body is not a valid JSON")
        if content_type == DATA_TYPE_MULTIPART:
            try:
                request_body = await request.form()
            except ValueError:
                raise HttpBadRequestError("Request body is not a valid multipart/form-data")

            operations = json.loads(request_body.get("operations", {}))
            files_map = json.loads(request_body.get('map', {}))
            request_files = {
                key: value for key, value in request_body.items()
                if isinstance(value, UploadFile)}
            result = place_files_in_operations(
                operations,
                files_map,
                request_files
            )
            return result

        raise HttpBadRequestError(
                "Posted content must be of type {} or {}".format(DATA_TYPE_JSON, DATA_TYPE_MULTIPART)
            )
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
        success, response = await graphql(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            debug=self.debug,
            logger=self.logger,
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

    async def handle_websocket_message(
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
        context_value = await self.get_context_for_request(websocket)
        success, results = await subscribe(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            debug=self.debug,
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
            subscriptions[operation_id] = results
            asyncio.ensure_future(
                self.observe_async_results(results, operation_id, websocket)
            )

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

        if websocket.application_state != WebSocketState.DISCONNECTED:
            await websocket.send_json({"type": GQL_COMPLETE, "id": operation_id})
