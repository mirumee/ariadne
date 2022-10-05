from typing import Any, Awaitable, Optional, Union


class APIExplorer:
    def html(self, request: Any) -> Union[Optional[str], Awaitable[Optional[str]]]:
        raise NotImplementedError("API explorer subclasses should define 'html' method")


class APIExplorerHttp405(APIExplorer):
    """API explorer that always returns HTTP 405 not found response."""

    def html(self, _):
        return None
