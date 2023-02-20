from asyncio import ensure_future
from inspect import isawaitable
from logging import Logger, LoggerAdapter
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Collection,
    List,
    Optional,
    Sequence,
    Type,
    cast,
    Union,
)
from warnings import warn

from graphql import (
    DocumentNode,
    ExecutionContext,
    ExecutionResult,
    GraphQLError,
    GraphQLSchema,
    MiddlewareManager,
    TypeInfo,
    execute,
    execute_sync,
    parse,
    subscribe as _subscribe,
)
from graphql.validation import specified_rules, validate
from graphql.validation.rules import ASTValidationRule

from .extensions import ExtensionManager
from .format_error import format_error
from .logger import log_error
from .types import (
    ErrorFormatter,
    ExtensionList,
    GraphQLResult,
    MiddlewareList,
    QueryParser,
    RootValue,
    SubscriptionResult,
    ValidationRules,
)
from .validation.introspection_disabled import IntrospectionDisabledRule


def root_value_two_args_deprecated():  # TODO: remove in 0.20
    warn(
        "'root_value(context, document)' has been deprecated and will raise a type "
        "error in Ariadne 0.20. Change definition to "
        "'root_value(context, operation_name, variables, document)'.",
        DeprecationWarning,
        stacklevel=2,
    )


async def graphql(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any] = None,
    root_value: Optional[RootValue] = None,
    query_parser: Optional[QueryParser] = None,
    query_document: Optional[DocumentNode] = None,
    debug: bool = False,
    introspection: bool = True,
    logger: Union[None, str, Logger, LoggerAdapter] = None,
    validation_rules: Optional[ValidationRules] = None,
    error_formatter: ErrorFormatter = format_error,
    middleware: MiddlewareList = None,
    middleware_manager_class: Optional[Type[MiddlewareManager]] = None,
    extensions: Optional[ExtensionList] = None,
    execution_context_class: Optional[Type[ExecutionContext]] = None,
    **kwargs,
) -> GraphQLResult:
    """Execute GraphQL query asynchronously.

    Returns a tuple with two items:

    `bool`: `True` when no errors occurred, `False` otherwise.

    `dict`: an JSON-serializable `dict` with query result
    (defining either `data`, `error`, or both keys) that should be returned to
    client.

    # Required arguments

    `schema`: a GraphQL schema instance that defines `Query` type.

    `data`: a `dict` with query data (`query` string, optionally `operationName`
    string and `variables` dictionary).

    # Optional arguments

    `context_value`: a context value to make accessible as 'context' attribute
    of second argument (`info`) passed to resolvers.

    `root_value`: a `RootValue` to pass as first argument to resolvers set on
    `Query` and `Mutation` types.

    `query_parser`: a `QueryParser` to use instead of default one. Is called
    with two arguments: `context_value`, and `data` dict.

    `query_document`: an already parsed GraphQL query. Setting this option will
    prevent `graphql` from parsing `query` string from `data` second time.

    `debug`: a `bool` for enabling debug mode. Controls presence of debug data
    in errors reported to client.

    `introspection`: a `bool` for disabling introspection queries.

    `logger`: a `str` with name of logger or logger instance to use for logging
    errors.

    `validation_rules`: a `list` of or callable returning list of custom
    validation rules to use to validate query before it's executed.

    `error_formatter`: an `ErrorFormatter` callable to use to convert GraphQL
    errors encountered during query execution to JSON-serializable format.

    `middleware`: a `list` of or callable returning list of GraphQL middleware
    to use by query executor.

    `middleware_manager_class`: a `MiddlewareManager` class to use by query
    executor.

    `extensions`: a `list` of or callable returning list of extensions
    to use during query execution.

    `execution_context_class`: `ExecutionContext` class to use by query
    executor.

    `**kwargs`: any kwargs not used by `graphql` are passed to
    `graphql.graphql`.
    """
    extension_manager = ExtensionManager(extensions, context_value)

    with extension_manager.request():
        try:
            validate_data(data)
            variables, operation_name = (
                data.get("variables"),
                data.get("operationName"),
            )

            if query_document:
                document = query_document
            else:
                document = parse_query(context_value, query_parser, data)

            if callable(validation_rules):
                validation_rules = cast(
                    Optional[Collection[Type[ASTValidationRule]]],
                    validation_rules(context_value, document, data),
                )

            validation_errors = validate_query(
                schema, document, validation_rules, enable_introspection=introspection
            )
            if validation_errors:
                return handle_graphql_errors(
                    validation_errors,
                    logger=logger,
                    error_formatter=error_formatter,
                    debug=debug,
                    extension_manager=extension_manager,
                )

            if callable(root_value):
                try:
                    root_value = root_value(  # type: ignore
                        context_value, operation_name, variables, document
                    )
                except TypeError:  # TODO: remove in 0.20
                    root_value_two_args_deprecated()
                    root_value = root_value(context_value, document)  # type: ignore

                if isawaitable(root_value):
                    root_value = await root_value

            result = execute(
                schema,
                document,
                root_value=root_value,
                context_value=context_value,
                variable_values=variables,
                operation_name=operation_name,
                execution_context_class=execution_context_class,
                middleware=extension_manager.as_middleware_manager(
                    middleware, middleware_manager_class
                ),
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
    query_parser: Optional[QueryParser] = None,
    query_document: Optional[DocumentNode] = None,
    debug: bool = False,
    introspection: bool = True,
    logger: Union[None, str, Logger, LoggerAdapter] = None,
    validation_rules: Optional[ValidationRules] = None,
    error_formatter: ErrorFormatter = format_error,
    middleware: MiddlewareList = None,
    middleware_manager_class: Optional[Type[MiddlewareManager]] = None,
    extensions: Optional[ExtensionList] = None,
    execution_context_class: Optional[Type[ExecutionContext]] = None,
    **kwargs,
) -> GraphQLResult:
    """Execute GraphQL query synchronously.

    Returns a tuple with two items:

    `bool`: `True` when no errors occurred, `False` otherwise.

    `dict`: an JSON-serializable `dict` with query result
    (defining either `data`, `error`, or both keys) that should be returned to
    client.

    # Required arguments

    `schema`: a GraphQL schema instance that defines `Query` type.

    `data`: a `dict` with query data (`query` string, optionally `operationName`
    string and `variables` dictionary).

    # Optional arguments

    `context_value`: a context value to make accessible as 'context' attribute
    of second argument (`info`) passed to resolvers.

    `root_value`: a `RootValue` to pass as first argument to resolvers set on
    `Query` and `Mutation` types.

    `query_parser`: a `QueryParser` to use instead of default one. Is called
    with two arguments: `context_value`, and `data` dict.

    `query_document`: an already parsed GraphQL query. Setting this option will
    prevent `graphql_sync` from parsing `query` string from `data` second time.

    `debug`: a `bool` for enabling debug mode. Controls presence of debug data
    in errors reported to client.

    `introspection`: a `bool` for disabling introspection queries.

    `logger`: a `str` with name of logger or logger instance to use for logging
    errors.

    `validation_rules`: a `list` of or callable returning list of custom
    validation rules to use to validate query before it's executed.

    `error_formatter`: an `ErrorFormatter` callable to use to convert GraphQL
    errors encountered during query execution to JSON-serializable format.

    `middleware`: a `list` of or callable returning list of GraphQL middleware
    to use by query executor.

    `middleware_manager_class`: a `MiddlewareManager` class to use by query
    executor.

    `extensions`: a `list` of or callable returning list of extensions
    to use during query execution.

    `execution_context_class`: `ExecutionContext` class to use by query
    executor.

    `**kwargs`: any kwargs not used by `graphql_sync` are passed to
    `graphql.graphql_sync`.
    """
    extension_manager = ExtensionManager(extensions, context_value)

    with extension_manager.request():
        try:
            validate_data(data)
            variables, operation_name = (
                data.get("variables"),
                data.get("operationName"),
            )

            if query_document:
                document = query_document
            else:
                document = parse_query(context_value, query_parser, data)

            if callable(validation_rules):
                validation_rules = cast(
                    Optional[Collection[Type[ASTValidationRule]]],
                    validation_rules(context_value, document, data),
                )

            validation_errors = validate_query(
                schema, document, validation_rules, enable_introspection=introspection
            )
            if validation_errors:
                return handle_graphql_errors(
                    validation_errors,
                    logger=logger,
                    error_formatter=error_formatter,
                    debug=debug,
                    extension_manager=extension_manager,
                )

            if callable(root_value):
                try:
                    root_value = root_value(  # type: ignore
                        context_value, operation_name, variables, document
                    )
                except TypeError:  # TODO: remove in 0.20
                    root_value_two_args_deprecated()
                    root_value = root_value(context_value, document)  # type: ignore

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
                execution_context_class=execution_context_class,
                middleware=extension_manager.as_middleware_manager(
                    middleware, middleware_manager_class
                ),
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
    query_parser: Optional[QueryParser] = None,
    query_document: Optional[DocumentNode] = None,
    debug: bool = False,
    introspection: bool = True,
    logger: Union[None, str, Logger, LoggerAdapter] = None,
    validation_rules: Optional[ValidationRules] = None,
    error_formatter: ErrorFormatter = format_error,
    **kwargs,
) -> SubscriptionResult:
    """Subscribe to GraphQL updates.

    Returns a tuple with two items:

    `bool`: `True` when no errors occurred, `False` otherwise.

    `AsyncGenerator`: an async generator that server implementation should
    consume to retrieve messages to send to client.

    # Required arguments

    'schema': a GraphQL schema instance that defines `Subscription` type.

    `data`: a `dict` with query data (`query` string, optionally `operationName`
    string and `variables` dictionary).

    # Optional arguments

    `context_value`: a context value to make accessible as 'context' attribute
    of second argument (`info`) passed to resolvers and source functions.

    `root_value`: a `RootValue` to pass as first argument to resolvers and
    source functions set on `Subscription` type.

    `query_parser`: a `QueryParser` to use instead of default one. Is called
    with two arguments: `context_value`, and `data` dict.

    `query_document`: an already parsed GraphQL query. Setting this option will
    prevent `subscribe` from parsing `query` string from `data` second time.

    `debug`: a `bool` for enabling debug mode. Controls presence of debug data
    in errors reported to client.

    `introspection`: a `bool` for disabling introspection queries.

    `logger`: a `str` with name of logger or logger instance to use for logging
    errors.

    `validation_rules`: a `list` of or callable returning list of custom
    validation rules to use to validate query before it's executed.

    `error_formatter`: an `ErrorFormatter` callable to use to convert GraphQL
    errors encountered during query execution to JSON-serializable format.

    `**kwargs`: any kwargs not used by `subscribe` are passed to
    `graphql.subscribe`.
    """
    try:
        validate_data(data)
        variables, operation_name = (
            data.get("variables"),
            data.get("operationName"),
        )

        if query_document:
            document = query_document
        else:
            document = parse_query(context_value, query_parser, data)

        if callable(validation_rules):
            validation_rules = cast(
                Optional[Collection[Type[ASTValidationRule]]],
                validation_rules(context_value, document, data),
            )

        validation_errors = validate_query(
            schema, document, validation_rules, enable_introspection=introspection
        )
        if validation_errors:
            for error_ in validation_errors:  # mypy issue #5080
                log_error(error_, logger)
            return (
                False,
                [error_formatter(error, debug) for error in validation_errors],
            )

        if callable(root_value):
            try:
                root_value = root_value(  # type: ignore
                    context_value, operation_name, variables, document
                )
            except TypeError:  # TODO: remove in 0.20
                root_value_two_args_deprecated()
                root_value = root_value(context_value, document)  # type: ignore

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

    if isinstance(result, ExecutionResult):
        errors = cast(List[GraphQLError], result.errors)
        for error_ in errors:  # mypy issue #5080
            log_error(error_, logger)
        return False, [error_formatter(error, debug) for error in errors]
    return True, cast(AsyncGenerator, result)


def handle_query_result(
    result, *, logger, error_formatter, debug, extension_manager=None
) -> GraphQLResult:
    response = {"data": result.data}
    if result.errors:
        for error in result.errors:
            log_error(error, logger)
        response["errors"] = [error_formatter(error, debug) for error in result.errors]

    if extension_manager:
        if result.errors:
            extension_manager.has_errors(result.errors)
        add_extensions_to_response(extension_manager, response)
    return True, response


def handle_graphql_errors(
    errors: Sequence[GraphQLError],
    *,
    logger: Union[None, str, Logger, LoggerAdapter],
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


def parse_query(
    context_value: Optional[Any],
    query_parser: Optional[QueryParser],
    data: Any,
) -> DocumentNode:
    try:
        if query_parser:
            return query_parser(context_value, data)

        return parse(data["query"])
    except GraphQLError as error:
        raise error
    except Exception as error:
        raise GraphQLError(str(error), original_error=error) from error


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
    rules: Optional[Collection[Type[ASTValidationRule]]] = None,
    max_errors: Optional[int] = None,
    type_info: Optional[TypeInfo] = None,
    enable_introspection: bool = True,
) -> List[GraphQLError]:
    if not enable_introspection:
        rules = (
            tuple(rules) + (IntrospectionDisabledRule,)
            if rules is not None
            else (IntrospectionDisabledRule,)
        )
    if rules:
        # run validation against rules from spec and custom rules
        supplemented_rules = specified_rules + tuple(rules)
        return validate(
            schema,
            document_ast,
            rules=supplemented_rules,
            max_errors=max_errors,
            type_info=type_info,
        )
    # run validation using spec rules only
    return validate(schema, document_ast, rules=specified_rules, type_info=type_info)


def validate_data(data: Optional[dict]) -> None:
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
