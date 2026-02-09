from abc import ABC, abstractmethod
from inspect import isawaitable
from logging import Logger, LoggerAdapter
from typing import Any, cast

from graphql import DocumentNode, ExecutionContext, GraphQLSchema, MiddlewareManager
from starlette.types import Receive, Scope, Send

from ...explorer import Explorer
from ...format_error import format_error
from ...types import (
    ContextValue,
    ErrorFormatter,
    GraphQLResult,
    OnComplete,
    OnConnect,
    OnDisconnect,
    OnOperation,
    QueryParser,
    QueryValidator,
    RootValue,
    ValidationRules,
)
from ...utils import context_value_one_arg_deprecated


class GraphQLHandler(ABC):
    """Base class for ASGI connection handlers."""

    def __init__(self) -> None:
        """Initialize the handler instance with an empty configuration."""
        self.schema: GraphQLSchema | None = None
        self.context_value: ContextValue | None = None
        self.debug: bool = False
        self.error_formatter: ErrorFormatter = format_error
        self.introspection: bool = True
        self.explorer: Explorer | None = None
        self.logger: None | str | Logger | LoggerAdapter = None
        self.root_value: RootValue | None = None
        self.query_parser: QueryParser | None = None
        self.query_validator: QueryValidator | None = None
        self.validation_rules: ValidationRules | None = None
        self.execute_get_queries: bool = False
        self.execution_context_class: type[ExecutionContext] | None = None
        self.middleware_manager_class: type[MiddlewareManager] | None = None

    @abstractmethod
    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """An entrypoint for the ASGI connection handler.

        This method is called by Ariadne ASGI GraphQL application. Subclasses
        should replace it with custom implementation.

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
        raise NotImplementedError(
            "Subclasses of GraphQLHandler must implement the 'handle' method."
        )

    def configure(
        self,
        schema: GraphQLSchema,
        context_value: ContextValue | None = None,
        root_value: RootValue | None = None,
        query_parser: QueryParser | None = None,
        query_validator: QueryValidator | None = None,
        validation_rules: ValidationRules | None = None,
        execute_get_queries: bool = False,
        debug: bool = False,
        introspection: bool = True,
        explorer: Explorer | None = None,
        logger: None | str | Logger | LoggerAdapter = None,
        error_formatter: ErrorFormatter = format_error,
        execution_context_class: type[ExecutionContext] | None = None,
    ):
        """Configures the handler with options from the ASGI application.

        Called by Ariadne ASGI GraphQL application as part of its
        initialization, propagating the configuration to it's handlers.
        """
        self.context_value = context_value
        self.debug = debug
        self.error_formatter = error_formatter
        self.execute_get_queries = execute_get_queries
        self.execution_context_class = execution_context_class
        self.introspection = introspection
        self.explorer = explorer
        self.logger = logger
        self.query_parser = query_parser
        self.query_validator = query_validator
        self.root_value = root_value
        self.schema = schema
        self.validation_rules = validation_rules

    async def get_context_for_request(
        self,
        request: Any,
        data: dict,
    ) -> Any:
        """Returns GraphQL context value for ASGI connection.

        Resolves final context value from the `ContextValue` value passed to
        `context_value` option. If `context_value` is None, sets default context
        value instead, which is a `dict` with single `request` key that contains
        either `starlette.requests.Request` instance or
        `starlette.websockets.WebSocket` instance.

        # Required arguments

        `request`: an instance of ASGI connection. It's type depends on handler.

        `data`: a GraphQL data from connection.
        """
        if callable(self.context_value):
            try:
                context = self.context_value(request, data)
            except TypeError:  # TODO: remove in 0.20
                context_value_one_arg_deprecated()
                context = cast(Any, self.context_value)(request)

            if isawaitable(context):
                context = await context
            return context

        return self.context_value or {"request": request}


class GraphQLHttpHandlerBase(GraphQLHandler):
    """Base class for ASGI HTTP connection handlers."""

    @abstractmethod
    async def handle_request(self, request: Any) -> Any:
        """Abstract method for handling the request.

        Should return valid ASGI response.
        """

    @abstractmethod
    async def execute_graphql_query(
        self,
        request: Any,
        data: Any,
        *,
        # Fast path for scenarios where context was already resolved
        # or query was already parsed
        context_value: Any | None = None,
        query_document: DocumentNode | None = None,
    ) -> GraphQLResult:
        """Abstract method for GraphQL query execution."""


class GraphQLWebsocketHandler(GraphQLHandler):
    """Base class for ASGI websocket connection handlers."""

    def __init__(
        self,
        on_connect: OnConnect | None = None,
        on_disconnect: OnDisconnect | None = None,
        on_operation: OnOperation | None = None,
        on_complete: OnComplete | None = None,
    ) -> None:
        """Initialize websocket handler with optional options specific to it.

        # Optional arguments:

        `on_connect`: an `OnConnect` callback used on new websocket connection.

        `on_disconnect`: an `OnDisconnect` callback used when existing
        websocket connection is closed.

        `on_operation`: an `OnOperation` callback, used when new GraphQL
        operation is received from websocket connection.

        `on_complete`: an `OnComplete` callback, used when GraphQL operation
        received over the websocket connection was completed.
        """
        super().__init__()
        self.http_handler: GraphQLHttpHandlerBase | None = None

        self.on_connect: OnConnect | None = on_connect
        self.on_disconnect: OnDisconnect | None = on_disconnect
        self.on_operation: OnOperation | None = on_operation
        self.on_complete: OnComplete | None = on_complete

    @abstractmethod
    async def handle_websocket(self, websocket: Any):
        """Abstract method for handling the websocket connection."""

    def configure(
        self,
        *args,
        http_handler: GraphQLHttpHandlerBase | None = None,
        **kwargs,
    ):
        """Configures the handler with options from the ASGI application.

        Called by Ariadne ASGI GraphQL application as part of its
        initialization, propagating the configuration to it's handlers.

        # Optional arguments

        `http_handler`: the `GraphQLHttpHandlerBase` subclass instance to use
        to execute the `Query` and `Mutation` operations made over the
        websocket connections.
        """
        super().configure(*args, **kwargs)
        self.http_handler = http_handler
