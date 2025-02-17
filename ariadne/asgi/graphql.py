from collections.abc import Awaitable
from logging import Logger, LoggerAdapter
from typing import Any, Optional, Union

from graphql import ExecutionContext, GraphQLSchema
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from ..explorer import Explorer, ExplorerGraphiQL
from ..format_error import format_error
from ..types import (
    ContextValue,
    ErrorFormatter,
    QueryParser,
    QueryValidator,
    RootValue,
    ValidationRules,
)
from .handlers import (
    GraphQLHTTPHandler,
    GraphQLWebsocketHandler,
    GraphQLWSHandler,
)


class GraphQL:
    """ASGI application implementing the GraphQL server.

    Can be used stand-alone or mounted within other ASGI application, for
    example in Starlette or FastAPI.
    """

    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        query_parser: Optional[QueryParser] = None,
        query_validator: Optional[QueryValidator] = None,
        validation_rules: Optional[ValidationRules] = None,
        execute_get_queries: bool = False,
        debug: bool = False,
        introspection: bool = True,
        explorer: Optional[Explorer] = None,
        logger: Union[None, str, Logger, LoggerAdapter] = None,
        error_formatter: ErrorFormatter = format_error,
        execution_context_class: Optional[type[ExecutionContext]] = None,
        http_handler: Optional[GraphQLHTTPHandler] = None,
        websocket_handler: Optional[GraphQLWebsocketHandler] = None,
    ) -> None:
        """Initializes the ASGI app and it's http and websocket handlers.

        # Required arguments

        `schema`: an instance of GraphQL schema to execute queries against.

        # Optional arguments

        `context_value`: a `ContextValue` to use by this server for context.
        Defaults to `{"request": request}` dictionary where `request` is
        an instance of `starlette.requests.Request`.

        `root_value`: a `RootValue` to use by this server for root value.
        Defaults to `None`.

        `query_parser`: a `QueryParser` to use by this server. Defaults to
        `graphql.parse`.

        `query_validator`: a `QueryValidator` to use by this server. Defaults to
        `graphql.validate`.

        `validation_rules`: a `ValidationRules` list or callable returning a
        list of extra validation rules server should use to validate the
        GraphQL queries. Defaults to `None`.

        `execute_get_queries`: a `bool` that controls if `query` operations
        sent using the `GET` method should be executed. Defaults to `False`.

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

        `execution_context_class`: custom `ExecutionContext` type to use by
        this server to execute the GraphQL queries. Defaults to standard
        context type implemented by the `graphql`.

        `http_handler`: an instance of `GraphQLHTTPHandler` class implementing
        the HTTP requests handling logic for this server. If not set,
        an instance of `GraphQLHTTPHandler` is used.

        `websocket_handler`: an instance of `GraphQLWebsocketHandler` class
        implementing the websocket connections handling logic for this server.
        If not set, `GraphQLWSHandler` will be used, implementing older
        version of GraphQL subscriptions protocol.
        """
        if http_handler:
            self.http_handler = http_handler
        else:
            self.http_handler = GraphQLHTTPHandler()

        if websocket_handler:
            self.websocket_handler = websocket_handler
        else:
            self.websocket_handler = GraphQLWSHandler()

        if not explorer:
            explorer = ExplorerGraphiQL()

        self.http_handler.configure(
            schema,
            context_value,
            root_value,
            query_parser,
            query_validator,
            validation_rules,
            execute_get_queries,
            debug,
            introspection,
            explorer,
            logger,
            error_formatter,
            execution_context_class,
        )
        self.websocket_handler.configure(
            schema,
            context_value,
            root_value,
            query_parser,
            query_validator,
            validation_rules,
            execute_get_queries,
            debug,
            introspection,
            explorer,
            logger,
            error_formatter,
            execution_context_class,
            http_handler=self.http_handler,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """An entrypoint to the ASGI application.

        Supports both HTTP and WebSocket connections.

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
        if scope["type"] == "http":
            await self.http_handler.handle(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.websocket_handler.handle(scope=scope, receive=receive, send=send)
        else:
            raise ValueError("Unknown scope type: {!r}".format(scope["type"]))

    async def handle_request(self, request: Request) -> Response:
        """Shortcut for `graphql_app.http_handler.handle_request(...)`."""
        return await self.http_handler.handle_request(request)

    async def handle_websocket(self, websocket: Any) -> Awaitable[Any]:
        """Shortcut for `graphql_app.websocket_handler.handle_websocket(...)`."""
        return await self.websocket_handler.handle_websocket(websocket)
