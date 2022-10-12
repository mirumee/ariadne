from typing import Any, Awaitable, Optional, Union


class Explorer:
    def html(self, request: Any) -> Union[Optional[str], Awaitable[Optional[str]]]:
        raise NotImplementedError("Explorer subclasses should define 'html' method")


class ExplorerHttp405(Explorer):
    """Explorer that always returns HTTP 405 not allowed response."""

    def html(self, _):
        return None
