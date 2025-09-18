from functools import reduce
from operator import add, mul
from typing import Any, Sequence, cast

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


CostAwareNode = (
    FieldNode
    | FragmentDefinitionNode
    | FragmentSpreadNode
    | InlineFragmentNode
    | OperationDefinitionNode
)


class CostValidator(ValidationRule):
    context: ValidationContext
    maximum_cost: int
    default_cost: int = 0
    default_complexity: int = 1
    variables: dict | None = None
    cost_map: dict[str, dict[str, Any]] | None = None

    def __init__(
        self,
        context: ValidationContext,
        maximum_cost: int,
        *,
        default_cost: int = 0,
        default_complexity: int = 1,
        variables: dict | None = None,
        cost_map: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(context)

        self.maximum_cost = maximum_cost
        self.variables = variables
        self.cost_map = cost_map
        self.default_cost = default_cost
        self.default_complexity = default_complexity
        self.cost = 0
        self.operation_multipliers: list[Any] = []

    def _get_field_cost(self, field, child_node, type_def, field_args):
        if self.cost_map:
            return self._cost_from_map(child_node, type_def, field_args)
        return self._cost_from_directives(field, field_args) or self._cost_from_type(
            field, field_args, type_def
        )

    def _cost_from_map(self, child_node, type_def, field_args):
        if not (type_def and type_def.name):
            return self.default_cost
        cost_map_args = self.get_args_from_cost_map(
            child_node, type_def.name, field_args
        )
        try:
            return self.compute_cost(**cost_map_args)
        except (TypeError, ValueError) as e:
            report_error(self.context, e)
            return self.default_cost

    def _cost_from_directives(self, field, field_args):
        if field.ast_node and field.ast_node.directives:
            directives_args = self.get_args_from_directives(
                field.ast_node.directives, field_args
            )
            if directives_args is not None:
                try:
                    return self.compute_cost(**directives_args)
                except (TypeError, ValueError) as e:
                    report_error(self.context, e)

    def _cost_from_type(self, field, field_args, type_def):
        if field_type and field_type.ast_node and field_type.ast_node.directives:
            if not cost_is_computed and isinstance(field_type, GraphQLObjectType):
                directives_args = self.get_args_from_directives(
                    field_type.ast_node.directives, field_args
                )
                if directives_args is not None:
                    try:
                        node_cost = self.compute_cost(**directives_args)
                    except (TypeError, ValueError) as e:
                        report_error(self.context, e)

    def compute_node_cost(self, node: CostAwareNode, type_def, parent_multipliers=None):
        if parent_multipliers is None:
            parent_multipliers = []
        if isinstance(node, FragmentSpreadNode) or not node.selection_set:
            return 0

        fields: GraphQLFieldMap = (
            type_def.fields
            if isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType))
            else {}
        )

        total = 0
        for child in node.selection_set.selections:
            node_cost = self.default_cost
            if isinstance(child, FieldNode):
                field = fields.get(child.name.value)
                if not field:
                    continue
                field_type = get_named_type(field.type)
                field_args = self._extract_field_args(field, child)
                node_cost = self._get_field_cost(field, child, type_def, field_args)
                node_cost += self.compute_node_cost(
                    child, field_type, parent_multipliers
                )
            elif isinstance(child, FragmentSpreadNode):
                node_cost = self._handle_fragment_spread(child, parent_multipliers)
            elif isinstance(child, InlineFragmentNode):
                node_cost = self._handle_inline_fragment(
                    child, type_def, parent_multipliers
                )
            total += node_cost
        return total

    def _extract_field_args(self, field, child):
        try:
            return get_argument_values(field, child, self.variables)
        except Exception as e:
            report_error(self.context, e)
            return {}

    def _handle_fragment_spread(self, child, multipliers):
        fragment = self.context.get_fragment(child.name.value)
        if not fragment:
            return 0
        ftype = self.context.schema.get_type(fragment.type_condition.name.value)
        return self.compute_node_cost(fragment, ftype, multipliers)

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

    def get_multipliers_from_string(
        self, multipliers: Sequence[str], field_args: dict[str, Any]
    ) -> list[int]:
        def get_deep_value(d: dict[str, Any], keys: Sequence[str]) -> Any:
            try:
                return reduce(
                    lambda c, k: c.get(k) if isinstance(c, dict) else None, keys, d
                )
            except AttributeError:
                return None

        parsed_vals: list[int] = []
        for acc_str in multipliers:
            keys = acc_str.split(".")
            val = get_deep_value(field_args, keys)
            if isinstance(val, (list, tuple)):
                parsed_vals.append(len(val))
            else:
                try:
                    intval = int(val)
                    if intval > 0:
                        parsed_vals.append(intval)
                except (ValueError, TypeError):
                    continue
        return parsed_vals

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
    variables: dict | None = None,
    cost_map: dict[str, dict[str, Any]] | None = None,
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
