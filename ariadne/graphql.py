from typing import Any, AsyncGenerator, List, Optional, Sequence, cast

import graphql as _graphql
from graphql import ExecutionResult, GraphQLError, GraphQLSchema, parse
from graphql.execution import Middleware

from .format_error import format_error
from .logger import log_error
from .types import ErrorFormatter, GraphQLResult, RootValue, SubscriptionResult


async def graphql(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    debug: bool = False,
    logger: Optional[str] = None,
    validation_rules=None,
    error_formatter: ErrorFormatter = format_error,
    middleware: Middleware = None,
    **kwargs,
) -> GraphQLResult:
    try:
        validate_data(data)
        query, variables, operation_name = (
            data["query"],
            data.get("variables"),
            data.get("operationName"),
        )
        document = parse(query)

        if validation_rules:
            errors = _graphql.validate(schema, document, validation_rules)
            if errors:
                return handle_graphql_errors(
                    errors, logger=logger, error_formatter=error_formatter, debug=debug
                )

        if callable(root_value):
            root_value = root_value(context_value, document)

        result = await _graphql.graphql(
            schema,
            query,
            root_value=root_value,
            context_value=context_value,
            variable_values=variables,
            operation_name=operation_name,
            middleware=middleware,
            **kwargs,
        )
    except GraphQLError as error:
        return handle_graphql_errors(
            [error], logger=logger, error_formatter=error_formatter, debug=debug
        )
    else:
        return handle_query_result(
            result, logger=logger, error_formatter=error_formatter, debug=debug
        )


def graphql_sync(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    debug: bool = False,
    logger: Optional[str] = None,
    validation_rules=None,
    error_formatter: ErrorFormatter = format_error,
    middleware: Middleware = None,
    **kwargs,
) -> GraphQLResult:
    try:
        validate_data(data)
        query, variables, operation_name = (
            data["query"],
            data.get("variables"),
            data.get("operationName"),
        )

        document = parse(query)

        if validation_rules:
            errors = _graphql.validate(schema, document, validation_rules)
            if errors:
                return handle_graphql_errors(
                    errors, logger=logger, error_formatter=error_formatter, debug=debug
                )

        if callable(root_value):
            root_value = root_value(context_value, document)

        result = _graphql.graphql_sync(
            schema,
            query,
            root_value=root_value,
            context_value=context_value,
            variable_values=variables,
            operation_name=operation_name,
            middleware=middleware,
            **kwargs,
        )
    except GraphQLError as error:
        return handle_graphql_errors(
            [error], logger=logger, error_formatter=error_formatter, debug=debug
        )
    else:
        return handle_query_result(
            result, logger=logger, error_formatter=error_formatter, debug=debug
        )


async def subscribe(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    debug: bool = False,
    logger: Optional[str] = None,
    validation_rules=None,
    error_formatter: ErrorFormatter = format_error,
    **kwargs,
) -> SubscriptionResult:
    try:
        validate_data(data)
        query, variables, operation_name = (
            data["query"],
            data.get("variables"),
            data.get("operationName"),
        )

        document = parse(query)

        if validation_rules:
            errors = _graphql.validate(schema, document, validation_rules)
            if errors:
                for error in errors:
                    log_error(error, logger)
                return False, [error_formatter(error, debug) for error in errors]

        if callable(root_value):
            root_value = root_value(context_value, document)

        result = await _graphql.subscribe(
            schema,
            document,
            root_value=root_value,
            context_value=context_value,
            variable_values=variables,
            operation_name=operation_name,
            **kwargs,
        )
    except GraphQLError as error:
        log_error(error, logger)
        return False, [error_formatter(error, debug)]
    else:
        if isinstance(result, ExecutionResult):
            errors = cast(List[GraphQLError], result.errors)
            for error_ in errors:  # mypy issue #5080
                log_error(error_, logger)
            return False, [error_formatter(error, debug) for error in errors]
        return True, cast(AsyncGenerator, result)


def handle_query_result(
    result, *, logger=None, error_formatter=format_error, debug=False
) -> GraphQLResult:
    response = {"data": result.data}
    if result.errors:
        for error in result.errors:
            log_error(error, logger)
        response["errors"] = [error_formatter(error, debug) for error in result.errors]
    return True, response


def handle_graphql_errors(
    errors: Sequence[GraphQLError], *, logger, error_formatter, debug
) -> GraphQLResult:
    for error in errors:
        log_error(error, logger)
    return False, {"errors": [error_formatter(error, debug) for error in errors]}


def validate_data(data: dict) -> None:
    if not isinstance(data, dict):
        raise GraphQLError("Operation data should be a JSON object")
    validate_query_body(data.get("query"))
    validate_variables(data.get("variables"))
    validate_operation_name(data.get("operationName"))


def validate_query_body(query) -> None:
    if not query or not isinstance(query, str):
        raise GraphQLError("The query must be a string.")


def validate_variables(variables) -> None:
    if variables is not None and not isinstance(variables, dict):
        raise GraphQLError("Query variables must be a null or an object.")


def validate_operation_name(operation_name) -> None:
    if operation_name is not None and not isinstance(operation_name, str):
        raise GraphQLError('"%s" is not a valid operation name.' % operation_name)
