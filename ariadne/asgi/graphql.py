from typing import Optional, Dict, Type
from datetime import timedelta

from graphql import GraphQLSchema
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from ..format_error import format_error
from .handlers import GraphQLTransportWS, GraphQLWS, GraphQLHTTP, GraphQLWebsocketBase
from ..types import (
    ContextValue,
    ErrorFormatter,
    RootValue,
    ValidationRules,
    Extensions,
    Middlewares,
    OnComplete,
    OnConnect,
    OnDisconnect,
    OnOperation,
    SubscriptionHandlers,
)


class GraphQL:
    def __init__(
        self,
        schema: GraphQLSchema,
        *,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        on_connect: Optional[OnConnect] = None,
        on_disconnect: Optional[OnDisconnect] = None,
        on_operation: Optional[OnOperation] = None,
        on_complete: Optional[OnComplete] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
        keepalive: float = None,
        connection_init_wait_timeout: timedelta = timedelta(minutes=1),
        subscription_handlers: Optional[
            SubscriptionHandlers[GraphQLWebsocketBase]
        ] = None,
    ):
        self.context_value = context_value
        self.root_value = root_value
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_operation = on_operation
        self.on_complete = on_complete
        self.validation_rules = validation_rules
        self.debug = debug
        self.introspection = introspection
        self.logger = logger
        self.error_formatter = error_formatter
        self.extensions = extensions
        self.middleware = middleware
        self.keepalive = keepalive
        self.schema = schema
        self.connection_init_wait_timeout = connection_init_wait_timeout
        if not subscription_handlers:
            self.subscription_handlers: Dict[str, Type[GraphQLWebsocketBase]] = {
                GraphQLTransportWS.PROTOCOL: GraphQLTransportWS,
                GraphQLWS.PROTOCOL: GraphQLWS,
            }
        else:
            self.subscription_handlers = dict(
                [(handler.PROTOCOL, handler) for handler in subscription_handlers]
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            await GraphQLHTTP(
                self.schema,
                context_value=self.context_value,
                root_value=self.root_value,
                validation_rules=self.validation_rules,
                debug=self.debug,
                introspection=self.introspection,
                logger=self.logger,
                error_formatter=self.error_formatter,
                extensions=self.extensions,
                middleware=self.middleware,
            ).handle_http(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            ws = WebSocket(scope=scope, receive=receive, send=send)
            detected_protocol = self.detect_protocol(ws)
            handler_class: Optional[Type[GraphQLWebsocketBase]] = (
                self.subscription_handlers.get(detected_protocol)
                if detected_protocol
                else None
            )

            if handler_class:
                await handler_class(
                    self.schema,
                    websocket=ws,
                    context_value=self.context_value,
                    root_value=self.root_value,
                    on_connect=self.on_connect,
                    on_disconnect=self.on_disconnect,
                    on_operation=self.on_operation,
                    on_complete=self.on_complete,
                    validation_rules=self.validation_rules,
                    debug=self.debug,
                    introspection=self.introspection,
                    logger=self.logger,
                    error_formatter=self.error_formatter,
                    extensions=self.extensions,
                    middleware=self.middleware,
                    connection_init_wait_timeout=self.connection_init_wait_timeout,
                    keepalive=self.keepalive,
                ).handle_websocket()
            else:
                await ws.close(code=4406)
        else:
            raise ValueError("Unknown scope type: %r" % (scope["type"],))

    def detect_protocol(self, ws: WebSocket) -> Optional[str]:
        ws_protocols = ws["subprotocols"]
        common_protocols = set(ws_protocols).intersection(
            self.subscription_handlers.keys()
        )
        ordered_protocols = sorted(common_protocols, key=ws_protocols.index)
        return ordered_protocols[0] if ordered_protocols else None
