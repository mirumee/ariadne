from reprlib import repr  # pylint: disable=redefined-builtin
from traceback import format_exception

from typing import List, Optional, cast

from graphql import GraphQLError

from .utils import unwrap_graphql_error


def format_error(error: GraphQLError, debug: bool = False) -> dict:
    """Format the GraphQL error into JSON serializable format.

    If `debug` is set to `True`, error's JSON will also include the `extensions`
    key with `exception` object containing error's `context` and `stacktrace`.

    Returns a JSON-serializable `dict` with error representation.

    # Required arguments

    `error`: an `GraphQLError` to convert into JSON serializable format.

    # Optional arguments

    `debug`: a `bool` that controls if debug data should be included in
    result `dict`. Defaults to `False`.
    """

    formatted = cast(dict, error.formatted)
    if debug:
        if "extensions" not in formatted:
            formatted["extensions"] = {}
        formatted["extensions"]["exception"] = get_error_extension(error)
    return formatted


def get_error_extension(error: GraphQLError) -> Optional[dict]:
    """Get a JSON-serializable `dict` containing error's stacktrace and context.

    Returns a JSON-serializable `dict` with `stacktrace` and `context` to include
    under error's `extensions` key in JSON response. Returns `None` if `error`
    has no stacktrace or wraps no exception.

    # Required arguments

    `error`: an `GraphQLError` to return context and stacktrace for.
    """
    unwrapped_error = unwrap_graphql_error(error)
    if unwrapped_error is None or not error.__traceback__:
        return None

    unwrapped_error = cast(Exception, unwrapped_error)
    return {
        "stacktrace": get_formatted_error_traceback(unwrapped_error),
        "context": get_formatted_error_context(unwrapped_error),
    }


def get_formatted_error_traceback(error: Exception) -> List[str]:
    """Get JSON-serializable stacktrace from `Exception`.

    Returns list of strings, with every item being separate line from stacktrace.

    This approach produces better results in GraphQL explorers which display every
    line under previous one but not always format linebreak characters for blocks
    of text.

    # Required arguments

    `error`: an `Exception` to return formatted stacktrace for.
    """
    formatted = []
    for line in format_exception(type(error), error, error.__traceback__):
        formatted.extend(line.rstrip().splitlines())
    return formatted


def get_formatted_error_context(error: Exception) -> Optional[dict]:
    """Get JSON-serializable context from `Exception`.

    Returns a `dict` of strings, with every key being value name and value
    being `repr()` of it's Python value. Returns `None` if context is not
    available.

    # Required arguments

    `error`: an `Exception` to return formatted context for.
    """

    tb_last = error.__traceback__
    while tb_last and tb_last.tb_next:
        tb_last = tb_last.tb_next
    if tb_last is None:
        return None
    return {key: repr(value) for key, value in tb_last.tb_frame.f_locals.items()}
