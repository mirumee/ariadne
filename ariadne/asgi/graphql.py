from typing import Optional

from starlette.responses import Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket

from .handlers import (
    GraphQLHTTPHandler,
    GraphQLWebsocketHandler,
)


class GraphQL:
    def __init__(
        self,
        http_handler: Optional[GraphQLHTTPHandler] = None,
        subscription_handler: Optional[GraphQLWebsocketHandler] = None,
    ):
        self.http_handler = http_handler
        self.subscription_handler = subscription_handler

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            if not self.http_handler:
                return await Response(status_code=400)(scope, receive, send)
            await self.http_handler.handle(scope=scope, receive=receive, send=send)
        elif scope["type"] == "websocket":
            if not self.subscription_handler:
                ws = WebSocket(scope=scope, receive=receive, send=send)
                await ws.close(code=4406)
            else:
                await self.subscription_handler.handle(
                    scope=scope, receive=receive, send=send
                )
        else:
            raise ValueError("Unknown scope type: %r" % (scope["type"],))
