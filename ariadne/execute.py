import asyncio
from inspect import isawaitable
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    NamedTuple,
    Optional,
    Set,
    Type,
    Union,
    cast,
)

from graphql import (
    DocumentNode,
    FieldNode,
    GraphQLError,
    GraphQLFieldResolver,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLTypeResolver,
    ResponsePath,
    response_path_as_list,
)
from graphql.language import FragmentDefinitionNode, OperationDefinitionNode
from graphql.execution.execute import (
    AwaitableOrValue,
    ExecutionContext,
    Middleware,
    MiddlewareManager,
    assert_valid_execution_arguments,
)


class DeferredResult(NamedTuple):
    """The result of a single @defer operation.

    - `data` is the result of a successful execution of the subquery.
    - `errors` is included when any errors occurred as a non-empty list.
    - `path` is the path to the subquery that was deferred.
    """

    data: Optional[Dict[str, Any]]
    errors: Optional[List[GraphQLError]]
    path: ResponsePath


class ExecutionResult(NamedTuple):
    """The result of GraphQL execution.

    - `data` is the result of a successful execution of the query.
    - `errors` is included when any errors occurred as a non-empty list.
    - `defers` is included when any of the fields were deferred.
    """

    data: Optional[Union[Dict[str, Any], AsyncGenerator[DeferredResult, None]]]
    errors: Optional[List[GraphQLError]]


def execute(
    schema: GraphQLSchema,
    document: DocumentNode,
    root_value: Any = None,
    context_value: Any = None,
    variable_values: Dict[str, Any] = None,
    operation_name: str = None,
    field_resolver: GraphQLFieldResolver = None,
    type_resolver: GraphQLTypeResolver = None,
    middleware: Middleware = None,
    execution_context_class: Type["ExecutionContext"] = None,
) -> AwaitableOrValue[ExecutionResult]:
    """Execute a GraphQL operation.

    Implements the "Evaluating requests" section of the GraphQL specification.

    Returns an ExecutionResult (if all encountered resolvers are synchronous),
    or a coroutine object eventually yielding an ExecutionResult.

    If the arguments to this function do not result in a legal execution context,
    a GraphQLError will be thrown immediately explaining the invalid input.
    """
    # If arguments are missing or incorrect, throw an error.
    assert_valid_execution_arguments(schema, document, variable_values)

    if execution_context_class is None:
        execution_context_class = DeferrableExecutionContext

    # If a valid execution context cannot be created due to incorrect arguments,
    # a "Response" with only errors is returned.
    exe_context = execution_context_class.build(
        schema,
        document,
        root_value,
        context_value,
        variable_values,
        operation_name,
        field_resolver,
        type_resolver,
        middleware,
    )

    # Return early errors if execution context failed.
    if isinstance(exe_context, list):
        return ExecutionResult(data=None, errors=exe_context)

    exe_context = cast(DeferrableExecutionContext, exe_context)
    # Return a possible coroutine object that will eventually yield the data described
    # by the "Response" section of the GraphQL specification.
    #
    # If errors are encountered while executing a GraphQL field, only that field and
    # its descendants will be omitted, and sibling fields will still be executed. An
    # execution which encounters errors will still result in a coroutine object that
    # can be executed without errors.

    data = exe_context.execute_operation(exe_context.operation, root_value)
    return exe_context.build_response(data)


class DeferrableExecutionContext(ExecutionContext):
    def __init__(
        self,
        schema: GraphQLSchema,
        fragments: Dict[str, FragmentDefinitionNode],
        root_value: Any,
        context_value: Any,
        operation: OperationDefinitionNode,
        variable_values: Dict[str, Any],
        field_resolver: GraphQLFieldResolver,
        type_resolver: GraphQLTypeResolver,
        middleware_manager: Optional[MiddlewareManager],
        errors: List[GraphQLError],
    ) -> None:
        super().__init__(
            schema,
            fragments,
            root_value,
            context_value,
            operation,
            variable_values,
            field_resolver,
            type_resolver,
            middleware_manager,
            errors,
        )
        self.defers: Set[asyncio.Future] = set()

    def build_response(self, data):
        if isawaitable(data):

            async def build_response_async():
                return self.build_response(await data)

            return build_response_async()
        data = cast(Optional[Dict[str, Any]], data)
        errors = self.errors
        if not errors:
            if self.defers:

                async def handle_defers():
                    yield data
                    done = set()
                    remaining = self.defers - done
                    while remaining:
                        # can't use `asyncio.as_completed` here as new defers may appear
                        (completed, _) = await asyncio.wait(
                            remaining, return_when=asyncio.FIRST_COMPLETED
                        )
                        for complete in completed:
                            yield await complete
                        done |= completed
                        remaining = self.defers - done

                return ExecutionResult(data=handle_defers(), errors=None)
            return ExecutionResult(data=data, errors=None)
        # Sort the error list in order to make it deterministic, since we might have
        # been using parallel execution.
        errors.sort(key=lambda error: (error.locations, error.path, error.message))

        return ExecutionResult(data=data, errors=errors)

    def resolve_field(
        self,
        parent_type: GraphQLObjectType,
        source: Any,
        field_nodes: List[FieldNode],
        path: ResponsePath,
    ) -> AwaitableOrValue[Any]:
        if field_nodes[0].directives:
            for directive in field_nodes[0].directives:
                if directive.name.value == "defer":

                    async def defer():
                        result = super(DeferrableExecutionContext, self).resolve_field(
                            parent_type, source, field_nodes, path
                        )
                        if isawaitable(result):
                            result = await result

                        return DeferredResult(
                            data=result, path=response_path_as_list(path), errors=None
                        )

                    task = asyncio.ensure_future(defer())
                    self.defers.add(task)

                    return None
        return super().resolve_field(parent_type, source, field_nodes, path)
