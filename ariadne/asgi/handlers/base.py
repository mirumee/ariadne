from abc import ABC, abstractmethod
from inspect import isawaitable
from typing import Any, Optional

from starlette.types import Receive, Scope, Send

from ariadne.types import ContextValue


class GraphQLHandler(ABC):
    def __init__(self, *_, **__):
        self.context_value: Optional[ContextValue]

    @abstractmethod
    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """Handle request"""

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


class GraphQLWebsocketHandler(GraphQLHandler):
    @abstractmethod
    async def handle(self, scope: Scope, receive: Receive, send: Send):
        """Handle request"""
