from traceback import format_exception


def handle_errors(result, extend_exception=False):
    return [format_error(e, extend_exception) for e in result.errors]


def format_error(error, extend_exception=False):
    formatted = error.formatted
    if extend_exception:
        if "extensions" not in formatted:
            formatted["extensions"] = {}
        formatted["extensions"]["exception"] = get_error_extension(error)
    return formatted


def get_error_extension(error):
    error = unwrap_graphql_error(error)
    return {
        "traceback": get_formatted_traceback(error),
        "context": get_formatted_context(error),
    }


def unwrap_graphql_error(error):
    try:
        # Unwrap GraphQLError or return it if there's no original error
        return unwrap_graphql_error(error.original_error) or error
    except AttributeError:
        return error


def get_formatted_traceback(error):
    formatted = format_exception(type(error), error, error.__traceback__)
    return [line.rstrip() for line in formatted]


def get_formatted_context(error):
    tb_last = error.__traceback__
    while tb_last.tb_next:
        tb_last = tb_last.tb_next
    return {key: repr(value) for key, value in tb_last.tb_frame.f_locals.items()}
