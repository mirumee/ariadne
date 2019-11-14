from asyncio import ensure_future
from inspect import isasyncgen, isawaitable
from typing import Any, AsyncGenerator, Awaitable, List, Optional, Sequence, Type, cast

from graphql import (
    DocumentNode,
    ExecutionContext,
    GraphQLError,
    GraphQLSchema,
    TypeInfo,
    parse,
)
from graphql import subscribe as _subscribe
from graphql.execution import MiddlewareManager
from graphql.execution import execute as execute_sync
from graphql.validation import specified_rules, validate
from graphql.validation.rules import RuleType

from .execute import (
    DeferrableExecutionContext,
    DeferredResult,
    ExecutionResult,
    execute,
)
from .extensions import ExtensionManager
from .format_error import format_error
from .logger import log_error
from .types import (
    ErrorFormatter,
    Extension,
    GraphQLResult,
    RootValue,
    SubscriptionResult,
)


async def graphql(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    debug: bool = False,
    logger: Optional[str] = None,
    validation_rules: Optional[Sequence[RuleType]] = None,
    error_formatter: ErrorFormatter = format_error,
    middleware: Optional[MiddlewareManager] = None,
    extensions: Optional[List[Type[Extension]]] = None,
    **kwargs,
) -> GraphQLResult:
    extension_manager = ExtensionManager(extensions, context_value)

    with extension_manager.request():
        try:
            validate_data(data)
            query, variables, operation_name = (
                data["query"],
                data.get("variables"),
                data.get("operationName"),
            )

            document = parse_query(query)

            validation_errors = validate_query(schema, document, validation_rules)
            if validation_errors:
                return handle_graphql_errors(
                    validation_errors,
                    logger=logger,
                    error_formatter=error_formatter,
                    debug=debug,
                    extension_manager=extension_manager,
                )

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
                execution_context_class=DeferrableExecutionContext,
                middleware=extension_manager.as_middleware_manager(middleware),
                **kwargs,
            )

            if isawaitable(result):
                result = await cast(Awaitable[ExecutionResult], result)
        except GraphQLError as error:
            return handle_graphql_errors(
                [error],
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
                extension_manager=extension_manager,
            )
        else:
            return handle_query_result(
                result,
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
                extension_manager=extension_manager,
            )


def graphql_sync(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    debug: bool = False,
    logger: Optional[str] = None,
    validation_rules: Optional[Sequence[RuleType]] = None,
    error_formatter: ErrorFormatter = format_error,
    middleware: Optional[MiddlewareManager] = None,
    extensions: Optional[List[Type[Extension]]] = None,
    **kwargs,
) -> GraphQLResult:
    extension_manager = ExtensionManager(extensions, context_value)

    with extension_manager.request():
        try:
            validate_data(data)
            query, variables, operation_name = (
                data["query"],
                data.get("variables"),
                data.get("operationName"),
            )

            document = parse_query(query)

            validation_errors = validate_query(schema, document, validation_rules)
            if validation_errors:
                return handle_graphql_errors(
                    validation_errors,
                    logger=logger,
                    error_formatter=error_formatter,
                    debug=debug,
                    extension_manager=extension_manager,
                )

            if callable(root_value):
                root_value = root_value(context_value, document)
                if isawaitable(root_value):
                    ensure_future(root_value).cancel()
                    raise RuntimeError(
                        "Root value resolver can't be asynchronous "
                        "in synchronous query executor."
                    )

            result = execute_sync(
                schema,
                document,
                root_value=root_value,
                context_value=context_value,
                variable_values=variables,
                operation_name=operation_name,
                execution_context_class=ExecutionContext,
                middleware=extension_manager.as_middleware_manager(middleware),
                **kwargs,
            )

            if isawaitable(result):
                ensure_future(cast(Awaitable[ExecutionResult], result)).cancel()
                raise RuntimeError(
                    "GraphQL execution failed to complete synchronously."
                )
        except GraphQLError as error:
            return handle_graphql_errors(
                [error],
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
                extension_manager=extension_manager,
            )
        else:
            return handle_query_result(
                result,
                logger=logger,
                error_formatter=error_formatter,
                debug=debug,
                extension_manager=extension_manager,
            )


async def subscribe(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    debug: bool = False,
    logger: Optional[str] = None,
    validation_rules: Optional[Sequence[RuleType]] = None,
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

        document = parse_query(query)

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
    result, *, logger, error_formatter, debug, extension_manager=None
) -> GraphQLResult:
    if not isasyncgen(result.data):
        response = {"data": result.data}
        if result.errors:
            for error in result.errors:
                log_error(error, logger)
            response["errors"] = [
                error_formatter(error, debug) for error in result.errors
            ]

        if extension_manager:
            if result.errors:
                extension_manager.has_errors(result.errors)
            add_extensions_to_response(extension_manager, response)

        return True, response

    async def handle_defers():
        async for chunk in result.data:
            if isinstance(chunk, DeferredResult):
                yield {"data": chunk.data, "path": chunk.path}
            else:
                yield {"data": chunk}

    return True, handle_defers()


def handle_graphql_errors(
    errors: Sequence[GraphQLError],
    *,
    logger,
    error_formatter,
    debug,
    extension_manager=None,
) -> GraphQLResult:
    for error in errors:
        log_error(error, logger)
    response = {"errors": [error_formatter(error, debug) for error in errors]}
    if extension_manager:
        extension_manager.has_errors(errors)
        add_extensions_to_response(extension_manager, response)
    return False, response


def parse_query(query):
    try:
        return parse(query)
    except GraphQLError as error:
        raise error
    except Exception as error:
        raise GraphQLError(str(error), original_error=error)


def add_extensions_to_response(extension_manager: ExtensionManager, response: dict):
    formatted_extensions = extension_manager.format()
    if formatted_extensions:
        if "extensions" in response:
            response["extensions"].update(formatted_extensions)
        else:
            response["extensions"] = formatted_extensions


def validate_query(
    schema: GraphQLSchema,
    document_ast: DocumentNode,
    rules: Optional[Sequence[RuleType]] = None,
    type_info: Optional[TypeInfo] = None,
) -> List[GraphQLError]:
    if rules:
        # run validation against rules from spec and custom rules
        return validate(
            schema,
            document_ast,
            rules=specified_rules + list(rules),
            type_info=type_info,
        )
    # run validation using spec rules only
    return validate(schema, document_ast, rules=specified_rules, type_info=type_info)


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


def validate_context_value(context_value) -> None:
    if callable(context_value):
        raise ValueError(
            "Callable context_value should be evaluated before query execution."
        )
