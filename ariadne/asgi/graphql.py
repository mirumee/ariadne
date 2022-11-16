from typing import Optional

from graphql import GraphQLSchema
from starlette.types import Receive, Scope, Send

from ..format_error import format_error
from ..types import (
    ContextValue,
    ErrorFormatter,
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
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
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

        self.http_handler.configure(
            schema,
            context_value,
            root_value,
            validation_rules,
            debug,
            introspection,
            logger,
            error_formatter,
        )
        self.websocket_handler.configure(
            schema,
            context_value,
            root_value,
            validation_rules,
            debug,
            introspection,
            logger,
            error_formatter,
            http_handler=self.http_handler,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await self.http_handler.handle(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            await self.websocket_handler.handle(scope=scope, receive=receive, send=send)
        else:
            raise ValueError("Unknown scope type: %r" % (scope["type"],))
