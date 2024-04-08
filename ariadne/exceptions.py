import os
from typing import Optional, Union

from .constants import HttpStatusResponse


class HttpError(Exception):
    """Base class for HTTP errors raised inside the ASGI and WSGI servers."""

    def __init__(self, status: str, message: Optional[str] = None) -> None:
        """Initializes the `HttpError` with a status and optional error message.

        # Arguments

        `status`: HTTP status code as `HttpStatusResponse`.
        `message`: Optional error message to return in the response body.
        """
        super().__init__()
        self.status = status
        self.message = message


class HttpBadRequestError(HttpError):
    """Raised when request did not contain the data required to execute
    the GraphQL query."""

    def __init__(self, message: Optional[str] = None) -> None:
        """Initializes the `HttpBadRequestError` with optional error message."""
        super().__init__(HttpStatusResponse.BAD_REQUEST.value, message)


class GraphQLFileSyntaxError(Exception):
    """Raised by `load_schema_from_path` when loaded GraphQL file has invalid syntax."""

    def __init__(self, file_path: Union[str, os.PathLike], message: str) -> None:
        """Initializes the `GraphQLFileSyntaxError` with file name and error.

        # Required arguments

        `file_path`: a `str` or `PathLike` object pointing to a file that
        failed to validate.

        `message`: a `str` with validation message.
        """
        super().__init__()

        self.message = self.format_message(file_path, message)

    def format_message(self, file_path: Union[str, os.PathLike], message: str):
        """Builds final error message from path to schema file and error message.

        Returns `str` with final error message.

        # Required arguments

        `file_path`: a `str` or `PathLike` object pointing to a file that
        failed to validate.

        `message`: a `str` with validation message.
        """
        return f"Could not load {file_path}:\n{message}"

    def __str__(self):
        """Returns error message."""
        return self.message


class WebSocketConnectionError(Exception):
    """Special error class enabling custom error reporting for on_connect"""

    def __init__(self, payload: Optional[Union[dict, str]] = None) -> None:
        if isinstance(payload, dict):
            self.payload = payload
        elif payload:
            self.payload = {"message": str(payload)}
        else:
            self.payload = {"message": "Unexpected error has occurred."}
