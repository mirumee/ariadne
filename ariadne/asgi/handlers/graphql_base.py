from inspect import isawaitable
from typing import Optional, Any, cast
from abc import ABC, abstractmethod

from graphql.execution import MiddlewareManager
from graphql import GraphQLSchema

from ...types import (
    ContextValue,
    GraphQLResult,
    ExtensionList,
    Extensions,
    Middlewares,
    ErrorFormatter,
    RootValue,
    ValidationRules,
)
from ...graphql import graphql


class GraphQLBase(ABC):
    def __init__(self, *_, **__):
        self.context_value: Optional[ContextValue]
        self.error_formatter: ErrorFormatter
        self.extensions: Optional[Extensions]
        self.middleware: Optional[Middlewares]
        self.schema: GraphQLSchema
        self.root_value: Optional[RootValue]
        self.validation_rules: Optional[ValidationRules]
        self.debug: bool
        self.introspection: bool
        self.logger: Optional[str]

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

    async def get_extensions_for_request(
        self, request: Any, context: Optional[ContextValue]
    ) -> ExtensionList:
        if callable(self.extensions):
            extensions = self.extensions(request, context)
            if isawaitable(extensions):
                extensions = await extensions  # type: ignore
            return extensions
        return self.extensions

    async def get_middleware_for_request(
        self, request: Any, context: Optional[ContextValue]
    ) -> Optional[MiddlewareManager]:
        middleware = self.middleware
        if callable(middleware):
            middleware = middleware(request, context)
            if isawaitable(middleware):
                middleware = await middleware  # type: ignore
        if middleware:
            middleware = cast(list, middleware)
            return MiddlewareManager(*middleware)
        return None

    async def execute_graphql_query(self, request: Any, data: Any) -> GraphQLResult:
        context_value = await self.get_context_for_request(request)
        extensions = await self.get_extensions_for_request(request, context_value)
        middleware = await self.get_middleware_for_request(request, context_value)

        return await graphql(
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


class GraphQLWebsocketBase(GraphQLBase):
    PROTOCOL: str

    @abstractmethod
    async def handle_websocket(self) -> None:
        """Handle websocket connection"""
