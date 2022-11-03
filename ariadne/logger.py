import logging
from typing import Union

from .utils import unwrap_graphql_error


def log_error(
    error: Exception,
    logger: Union[None, str, logging.Logger, logging.LoggerAdapter],
):
    original_error = unwrap_graphql_error(error)
    if original_error and original_error is not error:
        error.__suppress_context__ = True
        error.__cause__ = original_error

    if not logger:
        logger = "ariadne"
    if isinstance(logger, str):
        logger = logging.getLogger(logger)

    logger.error(error, exc_info=error)
