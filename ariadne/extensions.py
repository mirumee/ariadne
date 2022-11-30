from contextlib import contextmanager
from typing import List, Optional, Sequence, Type

from graphql import GraphQLError
from graphql.execution import Middleware, MiddlewareManager

from .types import ContextValue, ExtensionList


class ExtensionManager:
    __slots__ = ("context", "extensions", "extensions_reversed")

    def __init__(
        self,
        extensions: Optional[ExtensionList] = None,
        context: Optional[ContextValue] = None,
    ) -> None:
        self.context = context

        if extensions:
            self.extensions = tuple(ext() for ext in extensions)
            self.extensions_reversed = tuple(reversed(self.extensions))
        else:
            self.extensions_reversed = self.extensions = tuple()

    def as_middleware_manager(
        self,
        middleware: Optional[Sequence[Middleware]] = None,
        manager_class: Optional[Type[MiddlewareManager]] = None,
    ) -> Optional[MiddlewareManager]:
        if not middleware and not self.extensions:
            return None

        middleware = middleware or []
        if manager_class:
            return manager_class(*middleware, *self.extensions)

        return MiddlewareManager(*middleware, *self.extensions)

    @contextmanager
    def request(self):
        for ext in self.extensions:
            ext.request_started(self.context)
        try:
            yield
        finally:
            for ext in self.extensions_reversed:
                ext.request_finished(self.context)

    def has_errors(self, errors: List[GraphQLError]):
        for ext in self.extensions:
            ext.has_errors(errors, self.context)

    def format(self) -> dict:
        data = {}
        for ext in self.extensions:
            ext_data = ext.format(self.context)
            if ext_data:
                data.update(ext_data)
        return data
