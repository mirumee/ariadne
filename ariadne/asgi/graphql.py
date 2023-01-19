from logging import Logger, LoggerAdapter
from typing import Any, Awaitable, Optional, Type, Union

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
    RootValue,
    ValidationRules,
)
from .handlers import (
    GraphQLHTTPHandler,
    GraphQLWebsocketHandler,
    GraphQLWSHandler,
)


class GraphQL:
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
        logger: Union[None, str, Logger, LoggerAdapter] = None,
        error_formatter: ErrorFormatter = format_error,
        execution_context_class: Optional[Type[ExecutionContext]] = None,
        http_handler: Optional[GraphQLHTTPHandler] = None,
        websocket_handler: Optional[GraphQLWebsocketHandler] = None,
    ) -> None:
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
            validation_rules,
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
            validation_rules,
            debug,
            introspection,
            explorer,
            logger,
            error_formatter,
            execution_context_class,
            http_handler=self.http_handler,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.http_handler.handle(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.websocket_handler.handle(scope=scope, receive=receive, send=send)
        else:
            raise ValueError("Unknown scope type: %r" % (scope["type"],))

    def handle_request(self, request: Request) -> Awaitable[Response]:
        return self.http_handler.handle_request(request)

    async def handle_websocket(self, websocket: Any):
        return self.websocket_handler.handle_websocket(websocket)
