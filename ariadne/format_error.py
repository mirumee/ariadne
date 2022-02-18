from reprlib import repr  # pylint: disable=redefined-builtin
from traceback import format_exception

from typing import List, Optional, cast

from graphql import GraphQLError

from .utils import unwrap_graphql_error


def format_error(error: GraphQLError, debug: bool = False) -> dict:
    formatted = cast(dict, error.formatted)
    if debug:
        if "extensions" not in formatted:
            formatted["extensions"] = {}
        formatted["extensions"]["exception"] = get_error_extension(error)
    return formatted


def get_error_extension(error: GraphQLError) -> Optional[dict]:
    unwrapped_error = unwrap_graphql_error(error)
    if unwrapped_error is None or not error.__traceback__:
        return None

    unwrapped_error = cast(Exception, unwrapped_error)
    return {
        "stacktrace": get_formatted_error_traceback(unwrapped_error),
        "context": get_formatted_error_context(unwrapped_error),
    }


def get_formatted_error_traceback(error: Exception) -> List[str]:
    formatted = []
    for line in format_exception(type(error), error, error.__traceback__):
        formatted.extend(line.rstrip().splitlines())
    return formatted


def get_formatted_error_context(error: Exception) -> Optional[dict]:
    tb_last = error.__traceback__
    while tb_last and tb_last.tb_next:
        tb_last = tb_last.tb_next
    if tb_last is None:
        return None
    return {key: repr(value) for key, value in tb_last.tb_frame.f_locals.items()}
