import json
from http import HTTPStatus
from inspect import isawaitable
from typing import Any, Optional, Union, cast

from graphql import DocumentNode, MiddlewareManager
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send

from ...constants import (
    DATA_TYPE_JSON,
    DATA_TYPE_MULTIPART,
)
from ...exceptions import HttpBadRequestError, HttpError
from ...explorer import Explorer
from ...file_uploads import combine_multipart_data
from ...graphql import graphql
from ...types import (
    ContextValue,
    ExtensionList,
    Extensions,
    GraphQLResult,
    MiddlewareList,
    Middlewares,
)
from .base import GraphQLHttpHandlerBase


class GraphQLHTTPHandler(GraphQLHttpHandlerBase):
    """Default ASGI handler for HTTP requests.

    Supports the `Query` and `Mutation` operations.
    """

    def __init__(
        self,
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
        middleware_manager_class: Optional[type[MiddlewareManager]] = None,
    ) -> None:
        """Initializes the HTTP handler.

        # Optional arguments

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
        """
        super().__init__()

        self.extensions = extensions
        self.middleware = middleware
        self.middleware_manager_class = middleware_manager_class or MiddlewareManager

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        """An entrypoint for the GraphQL HTTP handler.

        This method is called by the Ariadne ASGI GraphQL application to execute
        queries done using the HTTP protocol.

        It creates the `starlette.requests.Request` instance, calls
        `handle_request` method with it, then sends response back to the client.

        # Required arguments

        `scope`: The connection scope information, a dictionary that contains
        at least a type key specifying the protocol that is incoming.

        `receive`: an awaitable callable that will yield a new event dictionary
        when one is available.

        `send`: an awaitable callable taking a single event dictionary as a
        positional argument that will return once the send has been completed
        or the connection has been closed.

        Details about the arguments and their usage are described in the
        ASGI specification:

        https://asgi.readthedocs.io/en/latest/specs/main.html
        """
        request = Request(scope=scope, receive=receive)
        response = await self.handle_request(request)
        await response(scope, receive, send)

    async def handle_request_override(self, _: Request) -> Optional[Response]:
        """Override the default request handling logic in subclasses.
        Is called in the `handle_request` method before the default logic.
        If None is returned, the default logic is executed.

         # Required arguments:
         `_`: the `Request` instance from Starlette or FastAPI.
        """
        return None

    async def handle_request(self, request: Request) -> Response:
        """Handle GraphQL request and return response for the client.

        Is called by the `handle` method and `handle_request` method of the
        ASGI GraphQL application.

        Handles three HTTP methods:

        `GET`: returns GraphQL explorer or 405 error response if explorer or
        introspection is disabled.

        `POST`: executes the GraphQL query from either `application/json` or
        `multipart/form-data` requests.

        `OPTIONS`: returns supported HTTP methods.

        Returns Starlette's `Response` instance, which is also works in FastAPI.

        # Required arguments:

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        response = await self.handle_request_override(request)
        if response is not None:
            return response

        if request.method == "GET":
            if self.execute_get_queries and request.query_params.get("query"):
                return await self.graphql_http_server(request)
            if self.introspection and self.explorer:
                # only render explorer when introspection is enabled
                return await self.render_explorer(request, self.explorer)

        if request.method == "POST":
            return await self.graphql_http_server(request)

        return self.handle_not_allowed_method(request)

    async def render_explorer(self, request: Request, explorer: Explorer) -> Response:
        """Return a HTML response with GraphQL explorer.

        # Required arguments:

        `request`: the `Request` instance from Starlette or FastAPI.

        `explorer`: an `Explorer` instance that implements the
        `html(request: Request)` method which returns either the `str` with HTML
        or `None`. If explorer returns `None`, `405` method not allowed response
        is returned instead.
        """
        explorer_html = explorer.html(request)
        if isawaitable(explorer_html):
            explorer_html = await explorer_html
        if explorer_html:
            return HTMLResponse(explorer_html)

        return self.handle_not_allowed_method(request)

    async def graphql_http_server(self, request: Request) -> Response:
        """Handles the HTTP request with GraphQL query.

        Extracts GraphQL query data from requests and then executes it using
        the `execute_graphql_query` method.

        Returns the JSON response from Sta

        If request's data was invalid or missing, plaintext response with
        error message and 400 status code is returned instead.

        # Required arguments:

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        try:
            data = await self.extract_data_from_request(request)
        except HttpError as error:
            return PlainTextResponse(
                error.message or error.status, status_code=HTTPStatus.BAD_REQUEST
            )

        success, result = await self.execute_graphql_query(request, data)
        return await self.create_json_response(request, result, success)

    async def extract_data_from_request(self, request: Request) -> Union[dict, list]:
        """Extracts GraphQL request data from request.

        Returns a `dict` or `list` with GraphQL query data that was not yet validated.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        content_type = request.headers.get("Content-Type", "")
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            return await self.extract_data_from_json_request(request)
        if content_type == DATA_TYPE_MULTIPART:
            return await self.extract_data_from_multipart_request(request)
        if (
            request.method == "GET"
            and self.execute_get_queries
            and request.query_params.get("query")
        ):
            return self.extract_data_from_get_request(request)

        raise HttpBadRequestError(
            f"Posted content must be of type {DATA_TYPE_JSON} or {DATA_TYPE_MULTIPART}"
        )

    async def extract_data_from_json_request(self, request: Request) -> dict:
        """Extracts GraphQL data from JSON request.

        Returns a `dict` with GraphQL query data that was not yet validated.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        try:
            return await request.json()
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError("Request body is not a valid JSON") from ex

    async def extract_data_from_multipart_request(
        self, request: Request
    ) -> Union[dict, list]:
        """Extracts GraphQL data from `multipart/form-data` request.

        Returns an unvalidated `dict` or `list` with GraphQL query data.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        try:
            request_body = await request.form()
        except ValueError as ex:
            raise HttpBadRequestError(
                "Request body is not a valid multipart/form-data"
            ) from ex

        try:
            operations = json.loads(cast(Any, request_body.get("operations")))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'operations' multipart field is not a valid JSON"
            ) from ex
        try:
            files_map = json.loads(cast(Any, request_body.get("map")))
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

    def extract_data_from_get_request(self, request: Request) -> dict:
        """Extracts GraphQL data from GET request's querystring.

        Returns a `dict` with GraphQL query data that was not yet validated.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        query = request.query_params["query"].strip()
        operation_name = request.query_params.get("operationName", "").strip()
        variables = request.query_params.get("variables", "").strip()

        clean_variables = None

        if variables:
            try:
                clean_variables = json.loads(variables)
            except (TypeError, ValueError) as ex:
                raise HttpBadRequestError(
                    "Variables query arg is not a valid JSON"
                ) from ex

        return {
            "query": query,
            "operationName": operation_name or None,
            "variables": clean_variables,
        }

    async def execute_graphql_query(
        self,
        request: Any,
        data: Any,
        *,
        context_value: Any = None,
        query_document: Optional[DocumentNode] = None,
    ) -> GraphQLResult:
        """Executes GraphQL query from `request` and returns `GraphQLResult`.

        Creates GraphQL `ContextValue`, initializes extensions and middlewares,
        then runs the `graphql` function from Ariadne to execute the query.

        # Requires arguments

        `request`: the `Request` instance from Starlette or FastAPI.

        `data`: a GraphQL data.

        # Optional arguments

        `context_value`: a `ContextValue` for this request.

        `query_document`: an already parsed GraphQL query. Setting this option
        will prevent `graphql` from parsing `query` string from `data` second time.
        """
        if context_value is None:
            context_value = await self.get_context_for_request(request, data)

        extensions = await self.get_extensions_for_request(request, context_value)
        middleware = await self.get_middleware_for_request(request, context_value)

        if self.schema is None:
            raise TypeError("schema is not set, call configure method to initialize it")

        if isinstance(request, Request):
            require_query = request.method == "GET"
        else:
            require_query = False

        return await graphql(
            self.schema,
            data,
            context_value=context_value,
            root_value=self.root_value,
            query_parser=self.query_parser,
            query_validator=self.query_validator,
            query_document=query_document,
            validation_rules=self.validation_rules,
            require_query=require_query,
            debug=self.debug,
            introspection=self.introspection,
            logger=self.logger,
            error_formatter=self.error_formatter,
            extensions=extensions,
            middleware=middleware,
            middleware_manager_class=self.middleware_manager_class,
            execution_context_class=self.execution_context_class,
        )

    async def get_extensions_for_request(
        self, request: Any, context: Optional[ContextValue]
    ) -> ExtensionList:
        """Returns extensions to use when handling the GraphQL request.

        Returns `ExtensionList`, a list of extensions to use or `None`.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.

        `context`: a `ContextValue` for this request.
        """
        if callable(self.extensions):
            extensions = self.extensions(request, context)
            if isawaitable(extensions):
                extensions = await extensions  # type: ignore
            return extensions
        return self.extensions

    async def get_middleware_for_request(
        self, request: Any, context: Optional[ContextValue]
    ) -> MiddlewareList:
        """Returns GraphQL middlewares to use when handling the GraphQL request.

        Returns `MiddlewareList`, a list of middlewares to use or `None`.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.

        `context`: a `ContextValue` for this request.
        """
        middleware = self.middleware
        if callable(middleware):
            middleware = middleware(request, context)
            if isawaitable(middleware):
                middleware = await middleware  # type: ignore
        if middleware:
            return cast(MiddlewareList, middleware)
        return None

    async def create_json_response(
        self,
        request: Request,
        result: dict,
        success: bool,
    ) -> Response:
        """Creates JSON response from GraphQL's query result.

        Returns Starlette's `JSONResponse` instance that's also compatible
        with FastAPI. If `success` is `True`, response's status code is 200.
        Status code 400 is used otherwise.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.

        `result`: a JSON-serializable `dict` with query result.

        `success`: a `bool` specifying if
        """
        status_code = HTTPStatus.OK if success else HTTPStatus.BAD_REQUEST
        return JSONResponse(result, status_code=status_code)

    def handle_not_allowed_method(self, request: Request):
        """Handles request for unsupported HTTP method.

        Returns 200 response for `OPTIONS` request and 405 response for other
        methods. All responses have empty body.

        # Required arguments

        `request`: the `Request` instance from Starlette or FastAPI.
        """
        allowed_methods = ["OPTIONS", "POST"]
        if self.introspection:
            allowed_methods.append("GET")
        allow_header = {"Allow": ", ".join(allowed_methods)}

        if request.method == "OPTIONS":
            return Response(headers=allow_header)

        return Response(status_code=HTTPStatus.METHOD_NOT_ALLOWED, headers=allow_header)
