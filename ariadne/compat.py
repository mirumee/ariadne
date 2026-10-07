"""Compatibility layer for differences between supported graphql-core versions."""

from typing import Any

from graphql import (
    DirectiveNode,
    FieldNode,
    GraphQLDirective,
    GraphQLField,
    version_info,
)
from graphql.execution import values as _values
from graphql.execution.values import get_argument_values as _get_argument_values

GRAPHQL_CORE_3_3 = version_info >= (3, 3)

# Imports below exist only in one of supported graphql-core versions
if GRAPHQL_CORE_3_3:
    # graphql-core 3.3 replaced `ExecutionContext` with `Executor`
    from graphql import Executor as ExecutionContext  # ty: ignore[unresolved-import]

    _EXECUTION_CONTEXT_CLASS_ARG = "executor_class"
else:
    from graphql import ExecutionContext  # ty: ignore[unresolved-import]

    _EXECUTION_CONTEXT_CLASS_ARG = "execution_context_class"


def get_execution_context_class_kwargs(
    execution_context_class: type[ExecutionContext] | None,
) -> dict[str, Any]:
    """Returns kwargs for graphql-core's `execute` with custom execution context.

    graphql-core 3.3 renamed `execution_context_class` argument to `executor_class`.
    """
    return {_EXECUTION_CONTEXT_CLASS_ARG: execution_context_class}


def get_argument_values(
    type_def: GraphQLField | GraphQLDirective,
    node: FieldNode | DirectiveNode,
    variable_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepares a dict of argument values for given field or directive node.

    Wraps graphql-core's `get_argument_values` to accept variables as `dict`
    regardless of graphql-core version used.
    """
    variables: Any = variable_values
    if GRAPHQL_CORE_3_3 and variable_values is not None:
        # graphql-core 3.3 expects variables wrapped in `VariableValues`
        variables = _values.VariableValues(  # ty: ignore[unresolved-attribute]
            sources={}, coerced=variable_values
        )
    return _get_argument_values(type_def, node, variables)


__all__ = [
    "GRAPHQL_CORE_3_3",
    "ExecutionContext",
    "get_argument_values",
    "get_execution_context_class_kwargs",
]
