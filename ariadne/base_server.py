from typing import Any, Optional, Sequence

import graphql
from graphql import GraphQLError, GraphQLSchema
from graphql.execution import Middleware
from graphql.validation.rules import RuleType

from .format_errors import format_error
from .types import ErrorFormatter, GraphQLSyncResult


def graphql_sync(
    schema: GraphQLSchema,
    data: Any,
    *,
    root_value: Any = None,
    context_value: Any = None,
    debug: bool = False,
    validation_rules=None,
    error_formatter: Optional[ErrorFormatter] = format_error,
    middleware: Middleware = None,
    **kwargs,
):
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

        result = graphql.graphql_sync(
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


def run_custom_validation(schema: GraphQLSchema, query: str, rules: Sequence[RuleType]):
    try:
        document_ast = parse(query)
    except:
        pass
    else:
        return graphql.validate(schema, document_ast, rules)


def handle_query_result(
    result, *, error_formatter=format_error, debug=False
) -> GraphQLSyncResult:
    response = {"data": result.data}
    if result.errors:
        response["errors"] = [error_formatter(error, debug) for error in result.errors]
    return 200, response


def handle_graphql_errors(
    errors: Sequence[GraphQLError], *, error_formatter, debug
) -> GraphQLSyncResult:
    return 400, {"errors": [error_formatter(error, debug) for error in errors]}


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
