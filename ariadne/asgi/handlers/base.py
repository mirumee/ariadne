from abc import ABC, abstractmethod
from inspect import isawaitable
from logging import Logger, LoggerAdapter
from typing import Any, Optional, Type, Union

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
        self.explorer: Optional[Explorer] = None
        self.logger: Union[None, str, Logger, LoggerAdapter] = None
        self.root_value: Optional[RootValue] = None
        self.query_parser: Optional[QueryParser] = None
        self.validation_rules: Optional[ValidationRules] = None
        self.execution_context_class: Optional[Type[ExecutionContext]] = None
        self.middleware_manager_class: Optional[Type[MiddlewareManager]] = None

    @abstractmethod
    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """Handle request"""

    def configure(
        self,
        schema: GraphQLSchema,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        query_parser: Optional[QueryParser] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        explorer: Optional[Explorer] = None,
        logger: Union[None, str, Logger, LoggerAdapter] = None,
        error_formatter: ErrorFormatter = format_error,
        execution_context_class: Optional[Type[ExecutionContext]] = None,
    ):
        self.context_value = context_value
        self.debug = debug
        self.error_formatter = error_formatter
        self.execution_context_class = execution_context_class
        self.introspection = introspection
        self.explorer = explorer
        self.logger = logger
        self.query_parser = query_parser
        self.root_value = root_value
        self.schema = schema
        self.validation_rules = validation_rules

    async def get_context_for_request(
        self,
        request: Any,
        data: dict,
    ) -> Any:
        if callable(self.context_value):
            context = self.context_value(request, data)
            if isawaitable(context):
                context = await context
            return context

        return self.context_value or {"request": request}


class GraphQLHttpHandlerBase(GraphQLHandler):
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
