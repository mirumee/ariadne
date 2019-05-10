import logging
from typing import Optional

from .utils import unwrap_graphql_error


def log_error(error: Exception, logger_name: Optional[str]):
    original_error = unwrap_graphql_error(error)
    if original_error and original_error is not error:
        error.__suppress_context__ = True
        error.__cause__ = original_error

    logger = logging.getLogger(logger_name or "ariadne")
    logger.error(error, exc_info=error)
