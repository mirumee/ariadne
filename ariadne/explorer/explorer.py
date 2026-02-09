from collections.abc import Awaitable
from typing import Any


class Explorer:
    def html(self, request: Any) -> str | None | Awaitable[str | None]:
        raise NotImplementedError("Explorer subclasses should define 'html' method")


class ExplorerHttp405(Explorer):
    """Explorer that always returns HTTP 405 not allowed response."""

    def html(self, request: Any) -> None:
        return None
