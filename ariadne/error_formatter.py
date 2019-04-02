from traceback import format_tb

SKIP_TRACEBACK_HEAD = 3


def format_error(error, debug=False):
    formatted = error.formatted
    if debug:
        if "extensions" not in formatted:
            formatted["extensions"] = {}
        formatted["extensions"]["exception"] = get_error_details(error)
    return formatted


def get_error_details(error):
    return list(get_formatted_error_traceback(error))


def unwrap_graphql_error(error):
    try:
        return unwrap_graphql_error(error.original_error)
    except AttributeError:
        return error


def get_formatted_error_traceback(error):
    traceback = format_tb(error.__traceback__)[SKIP_TRACEBACK_HEAD:]
    for stack_frame in traceback:
        location, line = stack_frame.splitlines()
        yield "%s:" % location.strip()
        yield line

    unwrapped_error = unwrap_graphql_error(error)
    yield "%s: %s" % (type(unwrapped_error).__name__, unwrapped_error)
