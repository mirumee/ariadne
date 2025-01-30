from abc import ABC, abstractmethod
from inspect import isawaitable
from logging import Logger, LoggerAdapter
from typing import Any, Optional, Union

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
        """Initialize the handler instance with empty configuration."""
        self.schema: Optional[GraphQLSchema] = None
        self.context_value: Optional[ContextValue] = None
        self.debug: bool = False
        self.error_formatter: ErrorFormatter = format_error
        self.introspection: bool = True
        self.explorer: Optional[Explorer] = None
        self.logger: Union[None, str, Logger, LoggerAdapter] = None
        self.root_value: Optional[RootValue] = None
        self.query_parser: Optional[QueryParser] = None
        self.query_validator: Optional[QueryValidator] = None
        self.validation_rules: Optional[ValidationRules] = None
        self.execute_get_queries: bool = False
        self.execution_context_class: Optional[type[ExecutionContext]] = None
        self.middleware_manager_class: Optional[type[MiddlewareManager]] = None

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
                context = self.context_value(request, data)  # type: ignore
            except TypeError:  # TODO: remove in 0.20
                context_value_one_arg_deprecated()
                context = self.context_value(request)  # type: ignore

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
        context_value: Optional[Any] = None,
        query_document: Optional[DocumentNode] = None,
    ) -> GraphQLResult:
        """Abstract method for GraphQL query execution."""


class GraphQLWebsocketHandler(GraphQLHandler):
    """Base class for ASGI websocket connection handlers."""

    def __init__(
        self,
        on_connect: Optional[OnConnect] = None,
        on_disconnect: Optional[OnDisconnect] = None,
        on_operation: Optional[OnOperation] = None,
        on_complete: Optional[OnComplete] = None,
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
        self.http_handler: Optional[GraphQLHttpHandlerBase] = None

        self.on_connect: Optional[OnConnect] = on_connect
        self.on_disconnect: Optional[OnDisconnect] = on_disconnect
        self.on_operation: Optional[OnOperation] = on_operation
        self.on_complete: Optional[OnComplete] = on_complete

    @abstractmethod
    async def handle_websocket(self, websocket: Any):
        """Abstract method for handling the websocket connection."""

    def configure(
        self,
        *args,
        http_handler: Optional[GraphQLHttpHandlerBase] = None,
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
