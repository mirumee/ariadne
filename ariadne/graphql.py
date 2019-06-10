from asyncio import ensure_future
from inspect import isawaitable
from typing import Any, AsyncGenerator, Awaitable, List, Optional, Sequence, cast

from graphql import (
    DocumentNode,
    ExecutionContext,
    ExecutionResult,
    GraphQLError,
    GraphQLSchema,
    TypeInfo,
    execute,
    parse,
    subscribe as _subscribe,
    validate_schema,
)
from graphql.execution import Middleware
from graphql.validation import specified_rules, validate
from graphql.validation.rules import RuleType

from .extensions_manager import ExtensionsManager
from .format_error import format_error
from .logger import log_error
from .types import (
    ErrorFormatter, Extension, GraphQLResult, RootValue, SubscriptionResult
)



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
    extensions: Optional[List[Extension]] = None,
    **kwargs,
) -> GraphQLResult:
    try:
        extensions_manager = ExtensionsManager(extensions)
        extensions_manager.execution_did_start()
        try:
            extensions_manager.validation_did_start()

            schema_validation_errors = None # validate_schema(schema)
            if schema_validation_errors:
                result = handle_graphql_errors(
                    schema_validation_errors,
                    logger=logger,
                    error_formatter=error_formatter,
                    debug=debug,
                )
                return extensions_manager.will_send_response(result)

            validate_data(data)
            query, variables, operation_name = (
                data["query"],
                data.get("variables"),
                data.get("operationName"),
            )

            if callable(context_value):
                context_value = context_value()

            # Parse
            try:
                extensions_manager.parsing_did_start(query)
                document = parse_query(query)
            finally:
                extensions_manager.parsing_did_end()

            validation_errors = validate_query(schema, document, validation_rules)
            if validation_errors:
                result = handle_graphql_errors(
                    validation_errors,
                    logger=logger,
                    error_formatter=error_formatter,
                    debug=debug,
                )
                return extensions_manager.will_send_response(result)
        finally:
            extensions_manager.validation_did_end()

        if callable(root_value):
            root_value = root_value(context_value, document)
            if isawaitable(root_value):
                root_value = await root_value

        result = execute(
            schema,
            document,
            root_value=root_value,
            context_value=context_value,
            variable_values=variables,
            operation_name=operation_name,
            execution_context_class=ExecutionContext,
            middleware=extensions_manager.as_middleware_manager(),
            **kwargs,
        )

        if isawaitable(result):
            result = await cast(Awaitable[ExecutionResult], result)
        extensions_manager.execution_did_end()
    except GraphQLError as error:
        result = handle_graphql_errors(
            [error], logger=logger, error_formatter=error_formatter, debug=debug
        )
    else:
        result = handle_query_result(
            result, logger=logger, error_formatter=error_formatter, debug=debug
        )
    return extensions_manager.will_send_response(result, context_value)


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
        schema_validation_errors = validate_schema(schema)
        if schema_validation_errors:
            return handle_graphql_errors(
                schema_validation_errors,
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
            )

        validate_data(data)
        query, variables, operation_name = (
            data["query"],
            data.get("variables"),
            data.get("operationName"),
        )

        if callable(context_value):
            context_value = context_value()

        # Parse
        document = parse_query(query)

        validation_errors = validate_query(schema, document, validation_rules)
        if validation_errors:
            return handle_graphql_errors(
                validation_errors,
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
            )

        if callable(root_value):
            root_value = root_value(context_value, document)
            if isawaitable(root_value):
                ensure_future(root_value).cancel()
                raise RuntimeError(
                    "Root value resolver can't be asynchronous "
                    "in synchronous query executor"
                )

        result = execute(
            schema,
            document,
            root_value=root_value,
            context_value=context_value,
            variable_values=variables,
            operation_name=operation_name,
            execution_context_class=ExecutionContext,
            **kwargs,
        )

        if isawaitable(result):
            ensure_future(cast(Awaitable[ExecutionResult], result)).cancel()
            raise RuntimeError("GraphQL execution failed to complete synchronously.")
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
        schema_validation_errors = validate_schema(schema)
        if schema_validation_errors:
            return handle_graphql_errors(
                schema_validation_errors,
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
            )

        validate_data(data)
        query, variables, operation_name = (
            data["query"],
            data.get("variables"),
            data.get("operationName"),
        )

        if callable(context_value):
            context_value = context_value()

        document = parse_query(query)

        if validation_rules:
            validation_errors = validate(schema, document, validation_rules)
            if validation_errors:
                for error_ in validation_errors:  # mypy issue #5080
                    log_error(error_, logger)
                return (
                    False,
                    [error_formatter(error, debug) for error in validation_errors],
                )

        if callable(root_value):
            root_value = root_value(context_value, document)
            if isawaitable(root_value):
                root_value = await root_value

        result = await _subscribe(
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


def parse_query(query):
    try:
        return parse(query)
    except GraphQLError as error:
        raise error
    except Exception as error:
        raise GraphQLError(str(error), original_error=error)


def validate_query(
    schema: GraphQLSchema,
    document_ast: DocumentNode,
    rules: Sequence[RuleType] = None,
    type_info: TypeInfo = None,
) -> List[GraphQLError]:
    if rules:
        # run validation against rules from spec and custom rules
        return validate(schema, document_ast, specified_rules + rules)
    # run validation using spec rules only
    return validate(schema, document_ast, specified_rules)


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
