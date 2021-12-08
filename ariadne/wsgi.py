import json
from cgi import FieldStorage
from typing import Any, Callable, List, Optional, Union

from graphql import GraphQLError, GraphQLSchema
from graphql.execution import Middleware, MiddlewareManager

from .constants import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT_HTML,
    CONTENT_TYPE_TEXT_PLAIN,
    DATA_TYPE_JSON,
    DATA_TYPE_MULTIPART,
    HTTP_STATUS_200_OK,
    HTTP_STATUS_400_BAD_REQUEST,
    HTTP_STATUS_405_METHOD_NOT_ALLOWED,
    PLAYGROUND_HTML,
)
from .exceptions import HttpBadRequestError, HttpError
from .file_uploads import combine_multipart_data
from .format_error import format_error
from .graphql import graphql_sync
from .types import (
    ContextValue,
    ErrorFormatter,
    ExtensionList,
    GraphQLResult,
    RootValue,
    ValidationRules,
)

Extensions = Union[
    Callable[[Any, Optional[ContextValue]], ExtensionList], ExtensionList
]
MiddlewareList = Optional[List[Middleware]]
Middlewares = Union[
    Callable[[Any, Optional[ContextValue]], MiddlewareList], MiddlewareList
]


class GraphQL:
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
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
    ) -> None:
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
        if environ["REQUEST_METHOD"] == "GET" and self.introspection:
            return self.handle_get(start_response)
        if environ["REQUEST_METHOD"] == "POST":
            return self.handle_post(environ, start_response)

        return self.handle_not_allowed_method(environ, start_response)

    def handle_get(self, start_response) -> List[bytes]:
        start_response(HTTP_STATUS_200_OK, [("Content-Type", CONTENT_TYPE_TEXT_HTML)])
        return [PLAYGROUND_HTML.encode("utf-8")]

    def handle_post(self, environ: dict, start_response: Callable) -> List[bytes]:
        data = self.get_request_data(environ)
        result = self.execute_query(environ, data)
        return self.return_response_from_result(start_response, result)

    def get_request_data(self, environ: dict) -> dict:
        content_type = environ.get("CONTENT_TYPE", "")
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            return self.extract_data_from_json_request(environ)
        if content_type == DATA_TYPE_MULTIPART:
            return self.extract_data_from_multipart_request(environ)

        raise HttpBadRequestError(
            "Posted content must be of type {} or {}".format(
                DATA_TYPE_JSON, DATA_TYPE_MULTIPART
            )
        )

    def extract_data_from_json_request(self, environ: dict) -> Any:
        request_content_length = self.get_request_content_length(environ)
        request_body = self.get_request_body(environ, request_content_length)

        try:
            return json.loads(request_body)
        except ValueError as ex:
            raise HttpBadRequestError("Request body is not a valid JSON") from ex

    def get_request_content_length(self, environ: dict) -> int:
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            if content_length < 1:
                raise HttpBadRequestError(
                    "Content length header is missing or incorrect"
                )
            return content_length
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Content length header is missing or incorrect"
            ) from ex

    def get_request_body(self, environ: dict, content_length: int) -> bytes:
        if not environ.get("wsgi.input"):
            raise HttpBadRequestError("Request body cannot be empty")
        request_body = environ["wsgi.input"].read(content_length)
        if not request_body:
            raise HttpBadRequestError("Request body cannot be empty")
        return request_body

    def extract_data_from_multipart_request(self, environ: dict) -> Any:
        try:
            form = FieldStorage(
                fp=environ["wsgi.input"], environ=environ, keep_blank_values=True
            )
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError("Malformed request data") from ex

        try:
            operations = json.loads(form.getvalue("operations"))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'operations' multipart field is not a valid JSON"
            ) from ex
        try:
            files_map = json.loads(form.getvalue("map"))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'map' multipart field is not a valid JSON"
            ) from ex

        return combine_multipart_data(operations, files_map, form)

    def execute_query(self, environ: dict, data: dict) -> GraphQLResult:
        context_value = self.get_context_for_request(environ)
        extensions = self.get_extensions_for_request(environ, context_value)
        middleware = self.get_middleware_for_request(environ, context_value)

        return graphql_sync(
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

    def get_context_for_request(self, environ: dict) -> Optional[ContextValue]:
        if callable(self.context_value):
            return self.context_value(environ)
        return self.context_value or {"request": environ}

    def get_extensions_for_request(
        self, environ: dict, context: Optional[ContextValue]
    ) -> ExtensionList:
        if callable(self.extensions):
            return self.extensions(environ, context)
        return self.extensions

    def get_middleware_for_request(
        self, environ: dict, context: Optional[ContextValue]
    ) -> Optional[MiddlewareManager]:
        middleware = self.middleware
        if callable(middleware):
            middleware = middleware(environ, context)
        if middleware:
            return MiddlewareManager(*middleware)
        return None

    def return_response_from_result(
        self, start_response: Callable, result: GraphQLResult
    ) -> List[bytes]:
        success, response = result
        status_str = HTTP_STATUS_200_OK if success else HTTP_STATUS_400_BAD_REQUEST
        start_response(status_str, [("Content-Type", CONTENT_TYPE_JSON)])
        return [json.dumps(response).encode("utf-8")]

    def handle_not_allowed_method(
        self, environ: dict, start_response: Callable
    ) -> List[bytes]:
        allowed_methods = ["OPTIONS", "POST"]
        if self.introspection:
            allowed_methods.append("GET")

        if environ["REQUEST_METHOD"] == "OPTIONS":
            status_str = HTTP_STATUS_200_OK
        else:
            status_str = HTTP_STATUS_405_METHOD_NOT_ALLOWED

        headers = [
            ("Content-Type", CONTENT_TYPE_TEXT_PLAIN),
            ("Content-Length", 0),
            ("Allow", ", ".join(allowed_methods)),
        ]

        start_response(status_str, headers)
        return []


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
