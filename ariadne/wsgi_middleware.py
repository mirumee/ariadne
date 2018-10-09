import json
from typing import Any, Callable, List, Optional, Union
from wsgiref.simple_server import make_server

from graphql import format_error, graphql
from graphql.execution import ExecutionResult

from .executable_schema import make_executable_schema
from .playground import PLAYGROUND_HTML

CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_TEXT_HTML = "text/html"
CONTENT_TYPE_TEXT_PLAIN = "text/plain"

HTTP_STATUS_200_OK = "200 OK"
HTTP_STATUS_400_BAD_REQUEST = "400 Bad Request"
HTTP_STATUS_405_METHOD_NOT_ALLOWED = "405 Method Not Allowed"


class HttpError(BaseException):
    status = ""

    def __init__(self, message=None):
        super().__init__()
        self.message = message


class HttpBadRequestError(HttpError):
    status = HTTP_STATUS_400_BAD_REQUEST


class HttpMethodNotAllowedError(HttpError):
    status = HTTP_STATUS_405_METHOD_NOT_ALLOWED


class GraphQLMiddleware:
    def __init__(
        self,
        app: Optional[Callable],
        type_defs: Union[str, List[str]],
        resolvers: Union[dict, List[dict]],
        path: str = "/graphql/",
    ) -> None:
        self.app = app
        self.path = path
        self.schema = make_executable_schema(type_defs, resolvers)

        if not path:
            raise ValueError("path keyword argument can't be empty")

        if app is not None and not callable(app):
            raise TypeError("first argument must be a callable or None")

        if not app and path != "/":
            raise TypeError(
                "can't set custom path on WSGI middleware without providing "
                "application callable as first argument"
            )

        if app and path == "/":
            raise ValueError(
                "WSGI middleware can't use root path together with "
                "application callable"
            )

    def __call__(self, environ: dict, start_response: Callable) -> List[bytes]:
        if self.app and not environ["PATH_INFO"].startswith(self.path):
            return self.app(environ, start_response)

        try:
            return self.handle_request(environ, start_response)
        except HttpError as error:
            return self.handle_http_error(start_response, error)

    def handle_http_error(
        self, start_response: Callable, error: HttpError
    ) -> List[bytes]:
        start_response(error.status, [("Content-Type", CONTENT_TYPE_TEXT_PLAIN)])
        response_body = error.message or error.status
        return [str(response_body).encode("utf-8")]

    def handle_request(self, environ: dict, start_response: Callable) -> List[bytes]:
        if environ["REQUEST_METHOD"] == "GET":
            return self.handle_get(start_response)
        if environ["REQUEST_METHOD"] == "POST":
            return self.handle_post(environ, start_response)
        raise HttpMethodNotAllowedError()

    def handle_get(self, start_response) -> List[bytes]:
        start_response(HTTP_STATUS_200_OK, [("Content-Type", CONTENT_TYPE_TEXT_HTML)])
        return [PLAYGROUND_HTML.encode("utf-8")]

    def handle_post(self, environ: dict, start_response: Callable) -> List[bytes]:
        data = self.get_request_data(environ)
        result = self.execute_query(environ, data)
        return self.return_response_from_result(start_response, result)

    def get_request_data(self, environ: dict) -> dict:
        if environ["CONTENT_TYPE"] != CONTENT_TYPE_JSON:
            raise HttpBadRequestError(
                "Posted content must be of type {}".format(CONTENT_TYPE_JSON)
            )

        request_content_length = self.get_request_content_length(environ)
        request_body = environ["wsgi.input"].read(request_content_length)
        if not request_body:
            raise HttpBadRequestError("request body cannot be empty")

        data = self.parse_request_body(request_body)
        if not isinstance(data, dict):
            raise HttpBadRequestError("valid request body should be a JSON object")

        return data

    def parse_request_body(self, request_body: bytes) -> Any:
        try:
            return json.loads(request_body)
        except (TypeError, ValueError):
            raise HttpBadRequestError("request body is not a valid JSON")

    def get_request_content_length(self, environ: dict) -> int:
        try:
            return int(environ.get("CONTENT_LENGTH", 0))
        except (TypeError, ValueError):
            raise HttpBadRequestError("content length header is missing or incorrect")

    def execute_query(self, environ: dict, data: dict) -> ExecutionResult:
        return graphql(
            self.schema,
            data.get("query"),
            root=self.get_query_root(environ, data),
            context=self.get_query_context(environ, data),
            variables=data.get("variables"),
            operation_name=data.get("operationName"),
        )

    def get_query_root(
        self, environ: dict, request_data: dict  # pylint: disable=unused-argument
    ) -> Any:
        """Override this method in inheriting class to create query root."""
        return None

    def get_query_context(
        self, environ: dict, request_data: dict  # pylint: disable=unused-argument
    ) -> Any:
        """Override this method in inheriting class to create query context."""
        return {"environ": environ}

    def return_response_from_result(
        self, start_response: Callable, result: ExecutionResult
    ) -> List[bytes]:
        status = HTTP_STATUS_200_OK
        response = {}
        if result.errors:
            response["errors"] = [format_error(e) for e in result.errors]
        if result.invalid:
            status = HTTP_STATUS_400_BAD_REQUEST
        else:
            response["data"] = result.data

        start_response(status, [("Content-Type", CONTENT_TYPE_JSON)])
        return [json.dumps(response).encode("utf-8")]

    @classmethod
    def make_simple_server(
        cls,
        type_defs: Union[str, List[str]],
        resolvers: Union[dict, List[dict]],
        host: str = "127.0.0.1",
        port: int = 8888,
    ):
        wsgi_app = cls(None, type_defs, resolvers, path="/")
        return make_server(host, port, wsgi_app)
