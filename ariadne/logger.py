import logging

from .utils import unwrap_graphql_error


logger = logging.getLogger("ariadne")


def log_error(error: Exception, logger):
    original_error = unwrap_graphql_error(error)
    if original_error and original_error is not error:
        error.__suppress_context__ = True
        error.__cause__ = original_error
    logger.error(error, exc_info=error)
