from traceback import format_exception

from typing import List, Optional

from graphql import ExecutionResult, GraphQLError


def default_error_handler(
    result: ExecutionResult, extend_exception: bool = False
) -> List[dict]:
    return [format_error(e, extend_exception) for e in result.errors]


def format_error(error: GraphQLError, extend_exception: bool = False) -> dict:
    formatted = error.formatted
    if extend_exception:
        if "extensions" not in formatted:
            formatted["extensions"] = {}
        formatted["extensions"]["exception"] = get_error_extension(error)
    return formatted


def get_error_extension(error: GraphQLError) -> Optional[dict]:
    error = unwrap_graphql_error(error)
    if not error:
        return None

    return {
        "traceback": get_formatted_traceback(error),
        "context": get_formatted_context(error),
    }


def unwrap_graphql_error(error: GraphQLError) -> Optional[Exception]:
    try:
        # Unwrap GraphQLError
        return unwrap_graphql_error(error.original_error)
    except AttributeError:
        return error


def get_formatted_traceback(error: Exception) -> List[str]:
    formatted = []
    for line in format_exception(type(error), error, error.__traceback__):
        formatted.extend(line.rstrip().splitlines())
    return formatted


def get_formatted_context(error: Exception) -> Optional[dict]:
    tb_last = error.__traceback__
    if not tb_last:
        return None
    while tb_last.tb_next:
        tb_last = tb_last.tb_next
    return {key: repr(value) for key, value in tb_last.tb_frame.f_locals.items()}
