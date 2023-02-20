import json
from inspect import isawaitable
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

from graphql import (
    ExecutionContext,
    GraphQLError,
    GraphQLSchema,
    MiddlewareManager,
)

from .constants import (
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT_HTML,
    CONTENT_TYPE_TEXT_PLAIN,
    DATA_TYPE_JSON,
    DATA_TYPE_MULTIPART,
    HTTP_STATUS_200_OK,
    HTTP_STATUS_400_BAD_REQUEST,
    HTTP_STATUS_405_METHOD_NOT_ALLOWED,
)
from .exceptions import HttpBadRequestError, HttpError
from .explorer import Explorer, ExplorerGraphiQL
from .file_uploads import combine_multipart_data
from .format_error import format_error
from .graphql import graphql_sync
from .types import (
    ContextValue,
    ErrorFormatter,
    ExtensionList,
    GraphQLResult,
    MiddlewareList,
    QueryParser,
    RootValue,
    ValidationRules,
)
from .utils import context_value_one_arg_deprecated

try:
    from multipart import parse_form
except ImportError:

    def parse_form(*_args, **_kwargs):
        raise NotImplementedError(
            "WSGI file uploads requires 'python-multipart' library."
        )


__all__ = ["FormData", "GraphQL", "GraphQLMiddleware"]

Extensions = Union[
    Callable[[Any, Optional[ContextValue]], ExtensionList], ExtensionList
]

Middlewares = Union[
    Callable[[Any, Optional[ContextValue]], MiddlewareList], MiddlewareList
]


class GraphQL:
    """WSGI application implementing the GraphQL server."""

    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        query_parser: Optional[QueryParser] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        explorer: Optional[Explorer] = None,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
        middleware_manager_class: Optional[Type[MiddlewareManager]] = None,
        execution_context_class: Optional[Type[ExecutionContext]] = None,
    ) -> None:
        """Initializes the WSGI app.

        # Required arguments

        `schema`: an instance of GraphQL schema to execute queries against.

        # Optional arguments

        `context_value`: a `ContextValue` to use by this server for context.
        Defaults to `{"request": request}` dictionary where `request` is
        an WSGI environment dictionary.

        `root_value`: a `RootValue` to use by this server for root value.
        Defaults to `None`.

        `query_parser`: a `QueryParser` to use by this server. Defaults to
        `graphql.parse`.

        `validation_rules`: a `ValidationRules` list or callable returning a
        list of extra validation rules server should use to validate the
        GraphQL queries. Defaults to `None`.

        `debug`: a `bool` controlling in server should run in debug mode or
        not. Controls details included in error data returned to clients.
        Defaults to `False`.

        `introspection`: a `bool` controlling if server should allow the
        GraphQL introspection queries. If `False`, introspection queries will
        fail to pass the validation. Defaults to `True`.

        `explorer`: an instance of `Explorer` subclass to use when the server
        receives an HTTP GET request. If not set, default GraphQL explorer
        for your version of Ariadne is used.

        `logger`: a `str` with name of logger or logger instance server
        instance should use for logging errors. If not set, a logger named
        `ariadne` is used.

        `error_formatter`: an `ErrorFormatter` this server should use to format
        GraphQL errors returned to clients. If not set, default formatter
        implemented by Ariadne is used.

        `extensions`: an `Extensions` list or callable returning a
        list of extensions server should use during query execution. Defaults
        to no extensions.

        `middleware`: a `Middlewares` list or callable returning a list of
        middlewares server should use during query execution. Defaults to no
        middlewares.

        `middleware_manager_class`: a `MiddlewareManager` type or subclass to
        use for combining provided middlewares into single wrapper for resolvers
        by the server. Defaults to `graphql.MiddlewareManager`. Is only used
        if `extensions` or `middleware` options are set.

        `execution_context_class`: custom `ExecutionContext` type to use by
        this server to execute the GraphQL queries. Defaults to standard
        context type implemented by the `graphql`.
        """

        self.context_value = context_value
        self.root_value = root_value
        self.query_parser = query_parser
        self.validation_rules = validation_rules
        self.debug = debug
        self.introspection = introspection
        self.logger = logger
        self.error_formatter = error_formatter
        self.extensions = extensions
        self.middleware = middleware
        self.middleware_manager_class = middleware_manager_class or MiddlewareManager
        self.execution_context_class = execution_context_class
        self.schema = schema

        if explorer:
            self.explorer = explorer
        else:
            self.explorer = ExplorerGraphiQL()

    def __call__(self, environ: dict, start_response: Callable) -> List[bytes]:
        """An entrypoint to the WSGI application.

        Returns list of bytes with response body.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `start_response`: a callable used to begin new HTTP response.

        Details about the arguments and their usage are described in PEP 3333:

        https://peps.python.org/pep-3333/
        """
        try:
            return self.handle_request(environ, start_response)
        except GraphQLError as error:
            return self.handle_graphql_error(error, start_response)
        except HttpError as error:
            return self.handle_http_error(error, start_response)

    def handle_graphql_error(
        self, error: GraphQLError, start_response: Callable
    ) -> List[bytes]:
        """Handles a `GraphQLError` raised from `handle_request` and returns an
        error response to the client.

        Returns list of bytes with response body.

        # Required arguments

        `error`: a `GraphQLError` instance.

        `start_response`: a callable used to begin new HTTP response.
        """
        start_response(
            HTTP_STATUS_400_BAD_REQUEST, [("Content-Type", CONTENT_TYPE_JSON)]
        )
        error_json = {"errors": [{"message": error.message}]}
        return [json.dumps(error_json).encode("utf-8")]

    def handle_http_error(
        self, error: HttpError, start_response: Callable
    ) -> List[bytes]:
        """Handles a `HttpError` raised from `handle_request` and returns an
        error response to the client.

        Returns list of bytes with response body.

        # Required arguments

        `error`: a `HttpError` instance.

        `start_response`: a callable used to begin new HTTP response.
        """
        start_response(error.status, [("Content-Type", CONTENT_TYPE_TEXT_PLAIN)])
        response_body = error.message or error.status
        return [str(response_body).encode("utf-8")]

    def handle_request(self, environ: dict, start_response: Callable) -> List[bytes]:
        """Handles WSGI HTTP request and returns a a response to the client.

        Returns list of bytes with response body.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `start_response`: a callable used to begin new HTTP response.
        """
        if environ["REQUEST_METHOD"] == "GET" and self.introspection:
            return self.handle_get(environ, start_response)
        if environ["REQUEST_METHOD"] == "POST":
            return self.handle_post(environ, start_response)

        return self.handle_not_allowed_method(environ, start_response)

    def handle_get(self, environ: dict, start_response) -> List[bytes]:
        """Handles WSGI HTTP GET request and returns a a response to the client.

        Returns list of bytes with response body.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `start_response`: a callable used to begin new HTTP response.
        """
        explorer_html = self.explorer.html(environ)
        if isawaitable(explorer_html):
            raise ValueError("Explorer HTML can't be awaitable.")
        if not explorer_html:
            return self.handle_not_allowed_method(environ, start_response)

        start_response(HTTP_STATUS_200_OK, [("Content-Type", CONTENT_TYPE_TEXT_HTML)])
        return [cast(str, explorer_html).encode("utf-8")]

    def handle_post(self, environ: dict, start_response: Callable) -> List[bytes]:
        """Handles WSGI HTTP POST request and returns a a response to the client.

        Returns list of bytes with response body.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `start_response`: a callable used to begin new HTTP response.
        """
        data = self.get_request_data(environ)
        result = self.execute_query(environ, data)
        return self.return_response_from_result(start_response, result)

    def get_request_data(self, environ: dict) -> dict:
        """Extracts GraphQL request data from request.

        Returns a `dict` with GraphQL query data that was not yet validated.

        # Required arguments

        `environ`: a WSGI environment dictionary.
        """
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
        """Extracts GraphQL data from JSON request.

        Returns a `dict` with GraphQL query data that was not yet validated.

        # Required arguments

        `environ`: a WSGI environment dictionary.
        """
        request_content_length = self.get_request_content_length(environ)
        request_body = self.get_request_body(environ, request_content_length)

        try:
            return json.loads(request_body)
        except ValueError as ex:
            raise HttpBadRequestError("Request body is not a valid JSON") from ex

    def get_request_content_length(self, environ: dict) -> int:
        """Validates and returns value from `Content-length` header.

        Returns an `int` with content length.

        Raises a `HttpBadRequestError` error if `Content-length` header is
        missing or invalid.

        # Required arguments

        `environ`: a WSGI environment dictionary.
        """
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
        """Returns request's body.

        Returns `bytes` with request body of specified length.

        Raises a `HttpBadRequestError` error if request body is empty.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `content_length`: an `int` with content length.
        """
        if not environ.get("wsgi.input"):
            raise HttpBadRequestError("Request body cannot be empty")
        request_body = environ["wsgi.input"].read(content_length)
        if not request_body:
            raise HttpBadRequestError("Request body cannot be empty")
        return request_body

    def extract_data_from_multipart_request(self, environ: dict) -> Any:
        """Extracts GraphQL data from `multipart/form-data` request.

        Returns an unvalidated `dict` with GraphQL query data.

        # Required arguments

        `environ`: a WSGI environment dictionary.
        """
        try:
            form = parse_multipart_request(environ)
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

        return combine_multipart_data(operations, files_map, form.files)

    def execute_query(self, environ: dict, data: dict) -> GraphQLResult:
        """Executes GraphQL query and returns its result.

        Returns a `GraphQLResult`, a two items long `tuple` with `bool` for
        success and JSON-serializable `data` to return to client.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `data`: a GraphQL data.
        """
        context_value = self.get_context_for_request(environ, data)
        extensions = self.get_extensions_for_request(environ, context_value)
        middleware = self.get_middleware_for_request(environ, context_value)

        return graphql_sync(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            query_parser=self.query_parser,
            validation_rules=self.validation_rules,
            debug=self.debug,
            introspection=self.introspection,
            logger=self.logger,
            error_formatter=self.error_formatter,
            extensions=extensions,
            middleware=middleware,
            middleware_manager_class=self.middleware_manager_class,
            execution_context_class=self.execution_context_class,
        )

    def get_context_for_request(
        self, environ: dict, data: dict
    ) -> Optional[ContextValue]:
        """Returns GraphQL context value for HTTP request.

        Default `ContextValue` for WSGI application is a `dict` with single
        `request` key that contains WSGI environment dictionary.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `data`: a GraphQL data.
        """
        if callable(self.context_value):
            try:
                return self.context_value(environ, data)  # type: ignore
            except TypeError:  # TODO: remove in 0.20
                context_value_one_arg_deprecated()
                return self.context_value(environ)  # type: ignore
        return self.context_value or {"request": environ}

    def get_extensions_for_request(
        self, environ: dict, context: Optional[ContextValue]
    ) -> ExtensionList:
        """Returns extensions to use when handling the GraphQL request.

        Returns `ExtensionList`, a list of extensions to use or `None`.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `context`: a `ContextValue` for this request.
        """
        if callable(self.extensions):
            return self.extensions(environ, context)
        return self.extensions

    def get_middleware_for_request(
        self, environ: dict, context: Optional[ContextValue]
    ) -> Optional[MiddlewareList]:
        """Returns GraphQL middlewares to use when handling the GraphQL request.

        Returns `MiddlewareList`, a list of middlewares to use or `None`.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `context`: a `ContextValue` for this request.
        """
        middleware = self.middleware
        if callable(middleware):
            middleware = middleware(environ, context)
        if middleware:
            return cast(MiddlewareList, middleware)
        return None

    def return_response_from_result(
        self, start_response: Callable, result: GraphQLResult
    ) -> List[bytes]:
        """Returns WSGI response from GraphQL result.

        Returns a list of bytes with response body.

        # Required arguments

        `start_response`: a WSGI callable that initiates new response.

        `result`: a `GraphQLResult` for this request.
        """
        success, response = result
        status_str = HTTP_STATUS_200_OK if success else HTTP_STATUS_400_BAD_REQUEST
        start_response(status_str, [("Content-Type", CONTENT_TYPE_JSON)])
        return [json.dumps(response).encode("utf-8")]

    def handle_not_allowed_method(
        self, environ: dict, start_response: Callable
    ) -> List[bytes]:
        """Handles request for unsupported HTTP method.

        Returns 200 response for `OPTIONS` request and 405 response for other
        methods. All responses have empty body.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `start_response`: a WSGI callable that initiates new response.
        """
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
    """Simple WSGI middleware routing requests to either app or GraphQL."""

    def __init__(
        self, app: Callable, graphql_app: Callable, path: str = "/graphql/"
    ) -> None:
        """Initializes the WSGI middleware.

        Returns response from either application or GraphQL application

        # Required arguments

        `app`: a WSGI application to route the request to if its path doesn't
        match the `path` option.

        `graphql_app`: a WSGI application to route the request to if its path
        matches the `path` option.

        # Optional arguments

        `path`: a `str` with a path to the GraphQL application. Defaults to
        `/graphql/`.
        """
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
        """An entrypoint to the WSGI middleware.

        Returns list of bytes with response body.

        # Required arguments

        `environ`: a WSGI environment dictionary.

        `start_response`: a callable used to start new HTTP response.
        """
        if not environ["PATH_INFO"].startswith(self.path):
            return self.app(environ, start_response)
        return self.graphql_app(environ, start_response)


def parse_multipart_request(environ: dict) -> "FormData":
    content_type = environ.get("CONTENT_TYPE")
    headers = {"Content-Type": content_type}
    form_data = FormData(content_type)

    parse_form(
        headers,
        environ["wsgi.input"],
        form_data.on_field,
        form_data.on_file,
    )

    return form_data


class FormData:
    """Feature-limited alternative of deprecated `cgi` standard package.

    Holds the data from `multipart/form-data` request.

    # Attributes

    `charset`: a string with charset extracted from `Content-type` header.
    Defaults to `latin-1`.

    `fields`: an `dict` with form's fields names and values.

    `files`: an `dict` with form's files names and values.
    """

    charset: str
    fields: Dict[str, Any]
    files: Dict[str, Any]

    def __init__(self, content_type: Optional[str]):
        """Initializes form data instance.

        # Optional arguments

        `content_type`: a string with content type header's value. If not
        provided, `latin-1` is used for content encoding.
        """
        self.encoding = self.parse_charset(content_type) or "latin-1"
        self.fields = {}
        self.files = {}

    def parse_charset(self, content_type: Optional[str]) -> Optional[str]:
        """Parses charset from `Content-type` header

        Returns none if `content_type` is not provided, empty or missing the
        `charset=` declaration.

        # Optional arguments

        `content_type`: a string with content type header's value.
        """
        if not content_type:
            return None

        if "charset=" not in content_type:
            return None

        charset = content_type[content_type.index("charset=") + 8 :].strip()
        if ";" in charset:
            charset = charset[: charset.index(";")].strip()

        return charset.lower() or None

    def on_field(self, field):
        """Callback for HTTP request parser to provide field data.

        Field name and value is decoded using the encoding stored in `encoding`
        attribute and stored in `fields` attribute.
        """
        field_name = field.field_name.decode(self.encoding)
        field_value = field.value.decode(self.encoding)
        self.fields[field_name] = field_value

    def on_file(self, file):
        """Callback for HTTP request parser to provide file data.

        File's field name is decoded using the encoding stored in `encoding`
        attribute and stored in `files` attribute.
        """
        field_name = file.field_name.decode(self.encoding)
        self.files[field_name] = file

    def getvalue(self, field_name: str) -> str:
        """Get form field's value.

        Returns field's value or empty string if field didn't exist.

        # Required arguments

        `field_name`: a `str` with name of form field to return the value for.
        """
        return self.fields.get(field_name, "")
