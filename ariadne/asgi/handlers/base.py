from abc import ABC, abstractmethod
from inspect import isawaitable
from typing import Any, Optional

from graphql import GraphQLSchema
from starlette.types import Receive, Scope, Send

from ...format_error import format_error
from ...types import (
    ContextValue,
    ErrorFormatter,
    GraphQLResult,
    OnComplete,
    OnConnect,
    OnDisconnect,
    OnOperation,
    RootValue,
    ValidationRules,
)


class GraphQLHandler(ABC):
    def __init__(self) -> None:
        self.schema: Optional[GraphQLSchema] = None
        self.context_value: Optional[ContextValue] = None
        self.debug: bool = False
        self.error_formatter: ErrorFormatter = format_error
        self.introspection: bool = True
        self.logger: Optional[str] = None
        self.root_value: Optional[RootValue] = None
        self.validation_rules: Optional[ValidationRules] = None

    @abstractmethod
    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """Handle request"""

    def configure(
        self,
        schema: GraphQLSchema,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
    ):
        self.context_value = context_value
        self.debug = debug
        self.error_formatter = error_formatter
        self.introspection = introspection
        self.logger = logger
        self.root_value = root_value
        self.schema = schema
        self.validation_rules = validation_rules

    async def get_context_for_request(
        self,
        request: Any,
    ) -> Any:
        if callable(self.context_value):
            context = self.context_value(request)
            if isawaitable(context):
                context = await context
            return context

        return self.context_value or {"request": request}


class GraphQLHttpHandlerBase(GraphQLHandler):
    @abstractmethod
    async def execute_graphql_query(self, request: Any, data: Any) -> GraphQLResult:
        """Execute query"""


class GraphQLWebsocketHandler(GraphQLHandler):
    def __init__(
        self,
        on_connect: Optional[OnConnect] = None,
        on_disconnect: Optional[OnDisconnect] = None,
        on_operation: Optional[OnOperation] = None,
        on_complete: Optional[OnComplete] = None,
    ) -> None:
        super().__init__()
        self.on_connect: Optional[OnConnect] = on_connect
        self.on_disconnect: Optional[OnDisconnect] = on_disconnect
        self.on_operation: Optional[OnOperation] = on_operation
        self.on_complete: Optional[OnComplete] = on_complete
        self.http_handler: Optional[GraphQLHttpHandlerBase] = None

    @abstractmethod
    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """Handle request"""

    def configure(
        self,
        *args,
        http_handler: Optional[GraphQLHttpHandlerBase] = None,
        **kwargs,
    ):
        super().configure(*args, **kwargs)
        self.http_handler = http_handler
