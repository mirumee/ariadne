import json
from logging import Logger
from typing import Any, Callable, List, Optional

from graphql import GraphQLError, GraphQLSchema

from .constants import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT_HTML,
    CONTENT_TYPE_TEXT_PLAIN,
    DATA_TYPE_JSON,
    HTTP_STATUS_200_OK,
    HTTP_STATUS_400_BAD_REQUEST,
    PLAYGROUND_HTML,
)
from .exceptions import HttpBadRequestError, HttpError, HttpMethodNotAllowedError
from .format_error import format_error
from .graphql import graphql_sync
from .logger import logger as default_logger
from .types import ContextValue, ErrorFormatter, GraphQLResult, RootValue


class GraphQL:
    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        debug: bool = False,
        logger: Optional[Logger] = None,
        error_formatter: ErrorFormatter = format_error,
        tracing: bool = False,
    ) -> None:
        self.context_value = context_value
        self.root_value = root_value
        self.debug = debug
        self.logger = logger or default_logger
        self.error_formatter = error_formatter
        self.schema = schema
        self.tracing = tracing

    def __call__(self, environ: dict, start_response: Callable) -> List[bytes]:
        try:
            return self.handle_request(environ, start_response)
        except GraphQLError as error:
            return self.handle_graphql_error(error, start_response)
        except HttpError as error:
            return self.handle_http_error(error, start_response)

    def handle_graphql_error(
        self, error: GraphQLError, start_response: Callable
    ) -> List[bytes]:
        start_response(
            HTTP_STATUS_400_BAD_REQUEST, [("Content-Type", CONTENT_TYPE_JSON)]
        )
        error_json = {"errors": [{"message": error.message}]}
        return [json.dumps(error_json).encode("utf-8")]

    def handle_http_error(
        self, error: HttpError, start_response: Callable
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
        if environ.get("CONTENT_TYPE") != DATA_TYPE_JSON:
            raise HttpBadRequestError(
                "Posted content must be of type {}".format(DATA_TYPE_JSON)
            )

        request_content_length = self.get_request_content_length(environ)
        request_body = self.get_request_body(environ, request_content_length)

        data = self.parse_request_body(request_body)
        if not isinstance(data, dict):
            raise GraphQLError("Valid request body should be a JSON object")

        return data

    def get_request_content_length(self, environ: dict) -> int:
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            if content_length < 1:
                raise HttpBadRequestError(
                    "Content length header is missing or incorrect"
                )
            return content_length
        except (TypeError, ValueError):
            raise HttpBadRequestError("Content length header is missing or incorrect")

    def get_request_body(self, environ: dict, content_length: int) -> bytes:
        if not environ.get("wsgi.input"):
            raise HttpBadRequestError("Request body cannot be empty")
        request_body = environ["wsgi.input"].read(content_length)
        if not request_body:
            raise HttpBadRequestError("Request body cannot be empty")
        return request_body

    def parse_request_body(self, request_body: bytes) -> Any:
        try:
            return json.loads(request_body)
        except ValueError:
            raise HttpBadRequestError("Request body is not a valid JSON")

    def execute_query(self, environ: dict, data: dict) -> GraphQLResult:
        tracing_requested = environ.get("X_APOLLO_TRACING") is not None
        return graphql_sync(
            self.schema,
            data,
            context_value=self.get_context_for_request(environ),
            root_value=self.root_value,
            debug=self.debug,
            logger=self.logger,
            tracing=self.tracing and tracing_requested,
            error_formatter=self.error_formatter,
        )

    def get_context_for_request(self, environ: dict) -> Any:
        if callable(self.context_value):
            return self.context_value(environ)
        return self.context_value or environ

    def return_response_from_result(
        self, start_response: Callable, result: GraphQLResult
    ) -> List[bytes]:
        success, response = result
        status_str = HTTP_STATUS_200_OK if success else HTTP_STATUS_400_BAD_REQUEST
        start_response(status_str, [("Content-Type", CONTENT_TYPE_JSON)])
        return [json.dumps(response).encode("utf-8")]


class GraphQLMiddleware:
    def __init__(
        self, app: Callable, graphql_app: Callable, path: str = "/graphql/"
    ) -> None:
        self.app = app
        self.path = path
        self.graphql_app = graphql_app

        if not callable(app):
            raise TypeError("app must be a callable WSGI application")

        if not path:
            raise ValueError("path can't be empty")

        if path == "/":
            raise ValueError(
                "WSGI middleware can't use root path together with "
                "application callable"
            )

    def __call__(self, environ: dict, start_response: Callable) -> List[bytes]:
        if not environ["PATH_INFO"].startswith(self.path):
            return self.app(environ, start_response)
        return self.graphql_app(environ, start_response)
