from typing import Dict, Type, cast, List

from graphql import (
    GraphQLError,
)
from graphql.language import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    Node,
    OperationDefinitionNode,
    OperationType,
    DefinitionNode,
)
from graphql.validation import ValidationContext
from graphql.validation.rules import ASTValidationRule, ValidationRule

from ..contrib.tracing.utils import is_introspection_key


def get_fragments(
    definitions: List[DefinitionNode],
) -> Dict[str, FragmentDefinitionNode]:
    fragments = {}
    for definition in definitions:
        if isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition
    return fragments


def determine_depth(
    node: Node,
    fragments: Dict[str, FragmentDefinitionNode],
    depth_so_far: int,
    max_depth: int,
    context: ValidationContext,
    operation_name: str,
) -> int:
    if depth_so_far > max_depth:
        context.report_error(
            GraphQLError(
                f"'{operation_name}' exceeds maximum operation depth of {max_depth}.",
                [node],
            )
        )
        return depth_so_far
    if isinstance(node, FieldNode):
        should_ignore = is_introspection_key(node.name.value)

        if should_ignore or not node.selection_set:
            return 0
        return 1 + max(
            map(
                lambda selection: determine_depth(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far + 1,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                ),
                node.selection_set.selections,
            )
        )
    elif isinstance(node, FragmentSpreadNode):
        return determine_depth(
            node=fragments[node.name.value],
            fragments=fragments,
            depth_so_far=depth_so_far,
            max_depth=max_depth,
            context=context,
            operation_name=operation_name,
        )
    elif isinstance(
        node, (InlineFragmentNode, FragmentDefinitionNode, OperationDefinitionNode)
    ):
        return max(
            map(
                lambda selection: determine_depth(
                    node=selection,
                    fragments=fragments,
                    depth_so_far=depth_so_far,
                    max_depth=max_depth,
                    context=context,
                    operation_name=operation_name,
                ),
                node.selection_set.selections,
            )
        )
    else:
        raise Exception(f"Depth crawler cannot handle: {node.kind}.")


class DepthLimitValidator(ValidationRule):
    context: ValidationContext
    maximum_cost: int

    def __init__(
        self,
        context: ValidationContext,
        maximum_depth: int,
    ):
        super().__init__(context)
        self.maximum_depth = maximum_depth
        document = context.document
        definitions = document.definitions

        self.fragments = get_fragments(definitions)

    def enter_operation_definition(
        self, node, key, parent, path, ancestors
    ):  # pylint: disable=unused-argument

        if (
            node.operation is OperationType.QUERY
            or node.operation is OperationType.MUTATION
        ):
            determine_depth(
                node=node,
                fragments=self.fragments,
                depth_so_far=0,
                max_depth=self.maximum_depth,
                context=self.context,
                operation_name=node.name.value if node.name else "anonymous",
            )


def depth_limit_validator(maximum_depth: int) -> Type[ASTValidationRule]:
    class _DepthLimitValidator(DepthLimitValidator):
        def __init__(self, context: ValidationContext):
            super().__init__(context, maximum_cost=maximum_depth)

    return cast(Type[ASTValidationRule], _DepthLimitValidator)
