from typing import Any, AsyncGenerator, Sequence, cast

import graphql as _graphql
from graphql import ExecutionResult, GraphQLError, GraphQLSchema, parse
from graphql.execution import Middleware
from graphql.validation.rules import RuleType

from .format_errors import format_error
from .types import ErrorFormatter, GraphQLResult, SubscriptionResult


async def graphql(
    schema: GraphQLSchema,
    data: Any,
    *,
    root_value: Any = None,
    context_value: Any = None,
    debug: bool = False,
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

        if validation_rules:
            errors = run_custom_validation(schema, query, validation_rules)
            if errors:
                return handle_graphql_errors(
                    errors, error_formatter=error_formatter, debug=debug
                )

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
            [error], error_formatter=error_formatter, debug=debug
        )
    else:
        return handle_query_result(result, error_formatter=error_formatter, debug=debug)


def graphql_sync(
    schema: GraphQLSchema,
    data: Any,
    *,
    root_value: Any = None,
    context_value: Any = None,
    debug: bool = False,
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

        if validation_rules:
            errors = run_custom_validation(schema, query, validation_rules)
            if errors:
                return handle_graphql_errors(
                    errors, error_formatter=error_formatter, debug=debug
                )

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
            [error], error_formatter=error_formatter, debug=debug
        )
    else:
        return handle_query_result(result, error_formatter=error_formatter, debug=debug)


async def subscribe(  # pylint: disable=too-complex
    schema: GraphQLSchema,
    data: Any,
    *,
    root_value: Any = None,
    context_value: Any = None,
    debug: bool = False,
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

        if validation_rules:
            errors = run_custom_validation(schema, query, validation_rules)
            if errors:
                return False, [error_formatter(error, debug) for error in errors]

        document = parse(query)
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
        return False, [error_formatter(error, debug)]
    else:
        if isinstance(result, ExecutionResult):
            return False, [error_formatter(error, debug) for error in result.errors]
        return True, cast(AsyncGenerator, result)


def run_custom_validation(
    schema: GraphQLSchema, query: str, rules: Sequence[RuleType]
) -> Sequence[GraphQLError]:
    try:
        document_ast = parse(query)
    except:  # pylint: disable=bare-except
        # Query does not validate
        return []
    else:
        return _graphql.validate(schema, document_ast, rules)


def handle_query_result(
    result, *, error_formatter=format_error, debug=False
) -> GraphQLResult:
    response = {"data": result.data}
    if result.errors:
        response["errors"] = [error_formatter(error, debug) for error in result.errors]
    return True, response


def handle_graphql_errors(
    errors: Sequence[GraphQLError], *, error_formatter, debug
) -> GraphQLResult:
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
