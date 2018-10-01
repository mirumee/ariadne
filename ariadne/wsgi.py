import json
from typing import Any, List, Union
from wsgiref.simple_server import make_server

from graphql import format_error, graphql
from graphql.execution import ExecutionResult

from .executable_schema import make_executable_schema
from .playground import PLAYGROUND_HTML

JSON_CONTENT_TYPE = "application/json"


class HttpException(Exception):
    status = ""


class Http400Exception(HttpException):
    status = "400 Bad Request"


class GraphQLMiddleware:
    def __init__(
        self, app, type_defs: Union[str, List[str]], resolvers: dict, path: str = "/"
    ) -> None:
        self.app = app
        self.path = path
        self.schema = make_executable_schema(type_defs, resolvers)

    def __call__(self, environ: dict, start_response) -> List[bytes]:
        if not environ["PATH_INFO"].startswith(self.path):
            return self.app(environ, start_response)

        try:
            return self.serve_request(environ, start_response)
        except HttpException as e:
            return self.error_response(start_response, e.status, e.args[0])

    def serve_request(self, environ: dict, start_response) -> List[bytes]:
        if environ["REQUEST_METHOD"] == "GET":
            return self.serve_playground(start_response)
        if environ["REQUEST_METHOD"] == "POST":
            return self.serve_query(environ, start_response)

        return self.error_response(start_response, "405 Method Not Allowed")

    def error_response(
        self, start_response, status: str, message: str = None
    ) -> List[bytes]:
        start_response(status, [("Content-Type", "text/plain")])
        final_message = message or status
        return [str(final_message).encode("utf-8")]

    def serve_playground(self, start_response) -> List[bytes]:
        start_response("200 OK", [("Content-Type", "text/html")])
        return [PLAYGROUND_HTML.encode("utf-8")]

    def serve_query(self, environ: dict, start_response) -> List[bytes]:
        data = self.get_request_data(environ)
        result = self.execute_query(environ, data)
        return self.return_response_from_result(start_response, result)

    def get_request_data(self, environ: dict) -> Any:
        if environ["CONTENT_TYPE"] != JSON_CONTENT_TYPE:
            raise Http400Exception(
                "Posted content must be of type {}".format(JSON_CONTENT_TYPE)
            )

        request_content_length = self.get_request_content_length(environ)
        request_body = environ["wsgi.input"].read(request_content_length)

        if not request_body:
            raise Http400Exception("request body cannot be empty")

        try:
            return json.loads(request_body)
        except (TypeError, ValueError):
            raise Http400Exception("request body is not a valid JSON")

    def get_request_content_length(self, environ) -> int:
        try:
            return int(environ.get("CONTENT_LENGTH", 0))
        except (TypeError, ValueError):
            raise Http400Exception("content length header is missing or incorrect")

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
        self, start_response, result: ExecutionResult
    ) -> List[bytes]:
        status = "200 OK"
        response = {}
        if result.errors:
            response["errors"] = [format_error(e) for e in result.errors]
        if result.invalid:
            status = "400 Bad Request"
        else:
            response["data"] = result.data

        start_response(status, [("Content-Type", JSON_CONTENT_TYPE)])
        return [json.dumps(response).encode("utf-8")]

    @classmethod
    def make_simple_server(
        cls, type_defs: Union[str, List[str]], resolvers: dict, port: int = 8888
    ):
        wsgi_app = cls(None, type_defs, resolvers)
        return make_server("0.0.0.0", port, wsgi_app)
