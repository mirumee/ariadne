from functools import reduce
from operator import add, mul
from typing import Any, Optional, Union, cast

from graphql import (
    GraphQLError,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    get_named_type,
)
from graphql.execution.values import get_argument_values
from graphql.language import (
    BooleanValueNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    IntValueNode,
    ListValueNode,
    Node,
    OperationDefinitionNode,
    OperationType,
    StringValueNode,
)
from graphql.type import GraphQLFieldMap
from graphql.validation import ValidationContext
from graphql.validation.rules import ASTValidationRule, ValidationRule

cost_directive = """
directive @cost(complexity: Int, multipliers: [String!], 
useMultipliers: Boolean) on FIELD | FIELD_DEFINITION
"""


CostAwareNode = Union[
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
]


class CostValidator(ValidationRule):
    context: ValidationContext
    maximum_cost: int
    default_cost: int = 0
    default_complexity: int = 1
    variables: Optional[dict] = None
    cost_map: Optional[dict[str, dict[str, Any]]] = None

    def __init__(
        self,
        context: ValidationContext,
        maximum_cost: int,
        *,
        default_cost: int = 0,
        default_complexity: int = 1,
        variables: Optional[dict] = None,
        cost_map: Optional[dict[str, dict[str, Any]]] = None,
    ) -> None:
        super().__init__(context)

        self.maximum_cost = maximum_cost
        self.variables = variables
        self.cost_map = cost_map
        self.default_cost = default_cost
        self.default_complexity = default_complexity
        self.cost = 0
        self.operation_multipliers: list[Any] = []

    def compute_node_cost(self, node: CostAwareNode, type_def, parent_multipliers=None):  # noqa C901
        if parent_multipliers is None:
            parent_multipliers = []
        if isinstance(node, FragmentSpreadNode) or not node.selection_set:
            return 0
        fields: GraphQLFieldMap = {}
        if isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType)):
            fields = type_def.fields
        total = 0
        for child_node in node.selection_set.selections:
            self.operation_multipliers = parent_multipliers[:]
            node_cost = self.default_cost
            if isinstance(child_node, FieldNode):
                field = fields.get(child_node.name.value)
                if not field:
                    continue
                field_type = get_named_type(field.type)
                try:
                    field_args: dict[str, Any] = get_argument_values(
                        field, child_node, self.variables
                    )
                except Exception as e:
                    report_error(self.context, e)
                    field_args = {}
                if self.cost_map:
                    cost_map_args = (
                        self.get_args_from_cost_map(
                            child_node, type_def.name, field_args
                        )
                        if type_def and type_def.name
                        else None
                    )
                    if cost_map_args is not None:
                        try:
                            node_cost = self.compute_cost(**cost_map_args)
                        except (TypeError, ValueError) as e:
                            report_error(self.context, e)
                else:
                    cost_is_computed = False
                    if field.ast_node and field.ast_node.directives:
                        directives_args = self.get_args_from_directives(
                            field.ast_node.directives, field_args
                        )
                        if directives_args is not None:
                            try:
                                node_cost = self.compute_cost(**directives_args)
                            except (TypeError, ValueError) as e:
                                report_error(self.context, e)
                            cost_is_computed = True
                    if (
                        field_type
                        and field_type.ast_node
                        and field_type.ast_node.directives
                    ):
                        if not cost_is_computed and isinstance(
                            field_type, GraphQLObjectType
                        ):
                            directives_args = self.get_args_from_directives(
                                field_type.ast_node.directives, field_args
                            )
                            if directives_args is not None:
                                try:
                                    node_cost = self.compute_cost(**directives_args)
                                except (TypeError, ValueError) as e:
                                    report_error(self.context, e)
                child_cost = self.compute_node_cost(
                    child_node, field_type, self.operation_multipliers
                )
                node_cost += child_cost
            if isinstance(child_node, FragmentSpreadNode):
                fragment = self.context.get_fragment(child_node.name.value)
                if fragment:
                    fragment_type = self.context.schema.get_type(
                        fragment.type_condition.name.value
                    )
                    node_cost = self.compute_node_cost(
                        fragment, fragment_type, self.operation_multipliers
                    )
            if isinstance(child_node, InlineFragmentNode):
                inline_fragment_type = type_def
                if child_node.type_condition and child_node.type_condition.name:
                    inline_fragment_type = self.context.schema.get_type(
                        child_node.type_condition.name.value
                    )
                node_cost = self.compute_node_cost(
                    child_node, inline_fragment_type, self.operation_multipliers
                )
            total += node_cost
        return total

    def enter_operation_definition(self, node, key, parent, path, ancestors):
        if self.cost_map:
            try:
                validate_cost_map(self.cost_map, self.context.schema)
            except GraphQLError as cost_map_error:
                self.context.report_error(cost_map_error)
                return

        if node.operation is OperationType.QUERY:
            self.cost += self.compute_node_cost(node, self.context.schema.query_type)
        if node.operation is OperationType.MUTATION:
            self.cost += self.compute_node_cost(node, self.context.schema.mutation_type)
        if node.operation is OperationType.SUBSCRIPTION:
            self.cost += self.compute_node_cost(
                node, self.context.schema.subscription_type
            )

    def leave_operation_definition(self, node, key, parent, path, ancestors):
        if self.cost > self.maximum_cost:
            self.context.report_error(self.get_cost_exceeded_error())

    def compute_cost(self, multipliers=None, use_multipliers=True, complexity=None):
        if complexity is None:
            complexity = self.default_complexity
        if use_multipliers:
            if multipliers:
                multiplier = reduce(add, multipliers, 0)
                self.operation_multipliers = self.operation_multipliers + [multiplier]
            return reduce(mul, self.operation_multipliers, complexity)
        return complexity

    def get_args_from_cost_map(
        self, node: FieldNode, parent_type: str, field_args: dict
    ):
        cost_args = None
        cost_map = cast(dict[Any, dict], self.cost_map)
        if parent_type in cost_map:
            cost_args = cost_map[parent_type].get(node.name.value)
        if not cost_args:
            return None
        cost_args = cost_args.copy()
        if "multipliers" in cost_args:
            cost_args["multipliers"] = self.get_multipliers_from_string(
                cost_args["multipliers"], field_args
            )
        return cost_args

    def get_args_from_directives(self, directives, field_args):
        cost_directive = next(
            (directive for directive in directives if directive.name.value == "cost"),
            None,
        )
        if cost_directive and cost_directive.arguments:
            complexity_arg = next(
                (
                    argument
                    for argument in cost_directive.arguments
                    if argument.name.value == "complexity"
                ),
                None,
            )
            use_multipliers_arg = next(
                (
                    argument
                    for argument in cost_directive.arguments
                    if argument.name.value == "useMultipliers"
                ),
                None,
            )
            multipliers_arg = next(
                (
                    argument
                    for argument in cost_directive.arguments
                    if argument.name.value == "multipliers"
                ),
                None,
            )
            use_multipliers = (
                use_multipliers_arg.value.value
                if use_multipliers_arg
                and use_multipliers_arg.value
                and isinstance(use_multipliers_arg.value, BooleanValueNode)
                else True
            )
            multipliers = (
                self.get_multipliers_from_list_node(
                    cast(list[Node], multipliers_arg.value.values), field_args
                )
                if multipliers_arg
                and multipliers_arg.value
                and isinstance(multipliers_arg.value, ListValueNode)
                else []
            )
            complexity = (
                int(complexity_arg.value.value)
                if complexity_arg
                and complexity_arg.value
                and isinstance(complexity_arg.value, IntValueNode)
                else None
            )
            return {
                "complexity": complexity,
                "multipliers": multipliers,
                "use_multipliers": use_multipliers,
            }

        return None

    def get_multipliers_from_list_node(self, multipliers: list[Node], field_args):
        multipliers = [
            node.value  # type: ignore
            for node in multipliers
            if isinstance(node, StringValueNode)
        ]
        return self.get_multipliers_from_string(multipliers, field_args)  # type: ignore

    def get_multipliers_from_string(self, multipliers: list[str], field_args):
        accessors = [s.split(".") for s in multipliers]
        multipliers = []
        for accessor in accessors:
            val = field_args
            for key in accessor:
                val = val.get(key)
            try:
                multipliers.append(int(val))  # type: ignore
            except (ValueError, TypeError):
                pass
        multipliers = [
            len(multiplier) if isinstance(multiplier, (list, tuple)) else multiplier
            for multiplier in multipliers
        ]
        return [m for m in multipliers if m > 0]  # type: ignore

    def get_cost_exceeded_error(self) -> GraphQLError:
        return GraphQLError(
            cost_analysis_message(self.maximum_cost, self.cost),
            extensions={
                "cost": {
                    "requestedQueryCost": self.cost,
                    "maximumAvailable": self.maximum_cost,
                }
            },
        )


def validate_cost_map(cost_map: dict[str, dict[str, Any]], schema: GraphQLSchema):
    for type_name, type_fields in cost_map.items():
        if type_name not in schema.type_map:
            raise GraphQLError(
                "The query cost could not be calculated because cost map specifies "
                f"a type {type_name} that is not defined by the schema."
            )

        if not isinstance(schema.type_map[type_name], GraphQLObjectType):
            raise GraphQLError(
                "The query cost could not be calculated because cost map specifies "
                f"a type {type_name} that is defined by the schema, "
                "but is not an object type."
            )

        for field_name in type_fields:
            graphql_type = cast(GraphQLObjectType, schema.type_map[type_name])
            if field_name not in graphql_type.fields:
                raise GraphQLError(
                    "The query cost could not be calculated because cost map contains "
                    f"a field {field_name} not defined by the {type_name} type."
                )


def report_error(context: ValidationContext, error: Exception):
    context.report_error(GraphQLError(str(error), original_error=error))


def cost_analysis_message(maximum_cost: int, cost: int) -> str:
    return (
        f"The query exceeds the maximum cost of {maximum_cost}. Actual cost is {cost}"
    )


def cost_validator(
    maximum_cost: int,
    *,
    default_cost: int = 0,
    default_complexity: int = 1,
    variables: Optional[dict] = None,
    cost_map: Optional[dict[str, dict[str, Any]]] = None,
) -> type[ASTValidationRule]:
    class _CostValidator(CostValidator):
        def __init__(self, context: ValidationContext) -> None:
            super().__init__(
                context,
                maximum_cost=maximum_cost,
                default_cost=default_cost,
                default_complexity=default_complexity,
                variables=variables,
                cost_map=cost_map,
            )

    return cast(type[ASTValidationRule], _CostValidator)
