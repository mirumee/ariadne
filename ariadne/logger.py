import logging

from graphql import GraphQLError

from .utils import unwrap_graphql_error


logger = logging.getLogger("ariadne")


def log_graphql_error(error: GraphQLError, logger):
    original_error = unwrap_graphql_error(error)
    if original_error:
        logger.exception(original_error)
    else:
        logger.error(error)
