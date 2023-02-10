from contextlib import contextmanager
from typing import List, Optional, Type

from graphql import GraphQLError
from graphql.execution import MiddlewareManager

from .types import MiddlewareList, ContextValue, ExtensionList


class ExtensionManager:
    """Container and runner for extensions and middleware, used by the GraphQL servers.

    # Attributes

    `context`: the `ContextValue` of type specific to the server.

    `extensions`: a `tuple` with instances of initialized extensions.

    `extensions_reversed`: a `tuple` created from reversing `extensions`.
    """

    __slots__ = ("context", "extensions", "extensions_reversed")

    def __init__(
        self,
        extensions: Optional[ExtensionList] = None,
        context: Optional[ContextValue] = None,
    ) -> None:
        """Initializes extensions and stores them with context on instance.

        # Optional arguments

        `extensions`: a `list` of `Extension` types to initialize.

        `context`: the `ContextValue` of type specific to the server.
        """
        self.context = context

        if extensions:
            self.extensions = tuple(ext() for ext in extensions)
            self.extensions_reversed = tuple(reversed(self.extensions))
        else:
            self.extensions_reversed = self.extensions = tuple()

    def as_middleware_manager(
        self,
        middleware: MiddlewareList = None,
        manager_class: Optional[Type[MiddlewareManager]] = None,
    ) -> Optional[MiddlewareManager]:
        """Creates middleware manager instance combining middleware and extensions.

        Returns instance of the type passed in `manager_class` argument
        or `MiddlewareManager` that query executor then uses.

        # Optional arguments

        `middleware`: a `list` of `Middleware` instances

        `manager_class` a `type` of middleware manager to use. `MiddlewareManager`
        is used if this argument is passed `None` or omitted.
        """
        if not middleware and not self.extensions:
            return None

        middleware = middleware or []
        if manager_class:
            return manager_class(*middleware, *self.extensions)

        return MiddlewareManager(*middleware, *self.extensions)

    @contextmanager
    def request(self):
        """A context manager that should wrap request processing.

        Runs `request_started` hook at beginning and `request_finished` at
        the end of request processing, enabling APM extensions like ApolloTracing.
        """
        for ext in self.extensions:
            ext.request_started(self.context)
        try:
            yield
        finally:
            for ext in self.extensions_reversed:
                ext.request_finished(self.context)

    def has_errors(self, errors: List[GraphQLError]):
        """Propagates GraphQL errors returned by GraphQL server to extensions.

        Should be called only when there are errors.
        """
        for ext in self.extensions:
            ext.has_errors(errors, self.context)

    def format(self) -> dict:
        """Gathers data from extensions for inclusion in server's response JSON.

        This data can be retrieved from the `extensions` key in response JSON.

        Returns `dict` with JSON-serializable data.
        """
        data = {}
        for ext in self.extensions:
            ext_data = ext.format(self.context)
            if ext_data:
                data.update(ext_data)
        return data
