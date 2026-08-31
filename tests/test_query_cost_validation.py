import pytest
from graphql import GraphQLError
from graphql.language import parse
from graphql.validation import validate

from ariadne import make_executable_schema
from ariadne.validation import cost_validator
from ariadne.validation.query_cost import CostValidator

cost_directive = """
directive @cost(
    complexity: Int, multipliers: [String!], useMultipliers: Boolean
) on FIELD | FIELD_DEFINITION
"""


@pytest.fixture
def schema():
    type_defs = """
        interface Other {
            name: String!
        }

        type Query {
            constant: Int!
            simple(value: Int!): Int!
            complex(valueA: Int, valueB: Int): Int!
            nested(value: NestedInput!): Int!
            child(value: Int!): [Child!]!
        }

        input NestedInput{
            num: Int!
        }

        type Child {
            name: String!
            online: Boolean!
        }
    """

    return make_executable_schema(type_defs)


@pytest.fixture
def schema_with_costs():
    type_defs = """
        type Query {
            constant: Int! @cost(complexity: 3)
            simple(value: Int!): Int! @cost(complexity: 1, multipliers: ["value"])
            complex(
                valueA: Int, valueB: Int
            ): Int! @cost(complexity: 1, multipliers: ["valueA", "valueB"])
            noComplexity(value: Int!): Int! @cost(multipliers: ["value"])
            nested(
                value: NestedInput!
            ): Int! @cost(complexity: 1, multipliers: ["value.num"])
            child(value: Int!): [Child!]! @cost(complexity: 1, multipliers: ["value"])
        }

        input NestedInput{
            num: Int!
        }

        type Child {
            name: String!
            online: Boolean! @cost(complexity: 3)
        }
    """

    return make_executable_schema([type_defs, cost_directive])


cost_map = {
    "Query": {
        "constant": {"complexity": 3},
        "simple": {"complexity": 1, "multipliers": ["value"]},
        "complex": {"complexity": 1, "multipliers": ["valueA", "valueB"]},
        "nested": {"complexity": 1, "multipliers": ["value.num"]},
        "child": {"complexity": 1, "multipliers": ["value"]},
    },
    "Child": {"online": {"complexity": 3}},
}


def test_cost_map_is_used_to_calculate_query_cost(schema):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 1. Actual cost is 3",
            extensions={"cost": {"requestedQueryCost": 3, "maximumAvailable": 1}},
        )
    ]


def test_query_validation_fails_if_cost_map_contains_undefined_type(schema):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1, cost_map={"Undefined": {"constant": 1}})
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query cost could not be calculated because cost map specifies a type "
            "Undefined that is not defined by the schema."
        )
    ]


def test_query_validation_fails_if_cost_map_contains_undefined_type_field(schema):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1, cost_map={"Query": {"undefined": 1}})
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query cost could not be calculated because cost map contains a field "
            "undefined not defined by the Query type."
        )
    ]


def test_query_validation_fails_if_cost_map_contains_non_object_type(schema):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1, cost_map={"Other": {"name": 1}})
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query cost could not be calculated because cost map specifies a type "
            "Other that is defined by the schema, but is not an object type."
        )
    ]


def test_cost_directive_is_used_to_calculate_query_cost(schema_with_costs):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 1. Actual cost is 3",
            extensions={"cost": {"requestedQueryCost": 3, "maximumAvailable": 1}},
        )
    ]


def test_field_cost_defined_in_map_is_multiplied_by_value_from_variables(schema):
    query = """
        query testQuery($value: Int!) {
            simple(value: $value)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5}, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_field_cost_defined_in_map_is_multiplied_by_nested_value_from_variables(schema):
    query = """
        query testQuery($value: NestedInput!) {
            nested(value: $value)
        }
    """
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=3, variables={"value": {"num": 5}}, cost_map=cost_map
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_field_cost_defined_in_map_is_multiplied_by_value_from_literal(schema):
    query = "{ simple(value: 5) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_value_from_variables(
    schema_with_costs,
):
    query = """
        query testQuery($value: Int!) {
            simple(value: $value)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_default_values_are_used_to_calculate_query_cost_without_directive_args(
    schema_with_costs,
):
    query = """
        query testQuery($value: Int!) {
            noComplexity(value: $value)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_nested_value_from_variables(
    schema_with_costs,
):
    query = """
        query testQuery($value: NestedInput!) {
            nested(value: $value)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": {"num": 5}})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_value_from_literal(
    schema_with_costs,
):
    query = "{ simple(value: 5) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_defined_in_map_is_multiplied_by_values_from_variables(
    schema,
):
    query = """
        query testQuery($valueA: Int, $valueB: Int) {
            complex(valueA: $valueA, valueB: $valueB)
        }
    """
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=3, variables={"valueA": 5, "valueB": 6}, cost_map=cost_map
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 11",
            extensions={"cost": {"requestedQueryCost": 11, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_defined_in_map_is_multiplied_by_values_from_literal(schema):
    query = "{ complex(valueA: 5, valueB: 6) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 11",
            extensions={"cost": {"requestedQueryCost": 11, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_multiplication_by_values_from_variables_handles_nulls(
    schema,
):
    query = """
        query testQuery($valueA: Int, $valueB: Int) {
            complex(valueA: $valueA, valueB: $valueB)
        }
    """
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=3, variables={"valueA": 5, "valueB": None}, cost_map=cost_map
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_multiplication_by_values_from_literals_handles_nulls(
    schema,
):
    query = "{ complex(valueA: 5, valueB: null) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_multiplication_by_values_from_variables_handles_optional(
    schema,
):
    query = """
        query testQuery($valueA: Int) {
            complex(valueA: $valueA)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"valueA": 5}, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_multiplication_by_values_from_literals_handles_optional(
    schema,
):
    query = "{ complex(valueA: 5) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_defined_in_directive_is_multiplied_by_values_from_variables(
    schema_with_costs,
):
    query = """
        query testQuery($valueA: Int, $valueB: Int) {
            complex(valueA: $valueA, valueB: $valueB)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"valueA": 5, "valueB": 6})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 11",
            extensions={"cost": {"requestedQueryCost": 11, "maximumAvailable": 3}},
        )
    ]


def test_complex_field_cost_defined_in_directive_is_multiplied_by_values_from_literal(
    schema_with_costs,
):
    query = "{ complex(valueA: 5, valueB: 6) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 11",
            extensions={"cost": {"requestedQueryCost": 11, "maximumAvailable": 3}},
        )
    ]


def test_child_field_cost_defined_in_map_is_multiplied_by_values_from_variables(schema):
    query = """
        query testQuery($value: Int!) {
            child(value: $value) { name online }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5}, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_field_cost_defined_in_map_is_multiplied_by_values_from_literal(schema):
    query = "{ child(value: 5) { name online } }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_field_cost_defined_in_directive_is_multiplied_by_values_from_variables(
    schema_with_costs,
):
    query = """
        query testQuery($value: Int!) {
            child(value: $value) { name online }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_field_cost_defined_in_directive_is_multiplied_by_values_from_literal(
    schema_with_costs,
):
    query = "{ child(value: 5) { name online } }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_inline_fragment_cost_defined_in_map_is_multiplied_by_values_from_variables(  # noqa: E501
    schema,
):
    query = """
        query testQuery($value: Int!) {
          child(value: $value) {
            ... on Child {
              online
            }
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5}, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_inline_fragment_cost_defined_in_map_is_multiplied_by_values_from_literal(
    schema,
):
    query = """
        {
          child(value: 5) {
            ... on Child{
                online
            }
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_inline_fragment_cost_defined_in_directive_is_multiplied_by_values_from_variables(  # noqa: E501
    schema_with_costs,
):
    query = """
        query testQuery($value: Int!) {
          child(value: $value) {
            ... on Child {
              online
            }
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_inline_fragment_cost_defined_in_directive_is_multiplied_by_values_from_literal(  # noqa: E501
    schema_with_costs,
):
    query = """
        {
          child(value: 5) {
            ... on Child{
                online
            }
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_fragment_cost_defined_in_map_is_multiplied_by_values_from_variables(
    schema,
):
    query = """
        fragment child on Child {
          online
        }
        query testQuery($value: Int!) {
          child(value: $value) {
            ...child
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5}, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_fragment_cost_defined_in_map_is_multiplied_by_values_from_literal(
    schema,
):
    query = """
        fragment child on Child {
          online
        }
        {
          child(value: 5) {
            ...child
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_fragment_cost_defined_in_directive_is_multiplied_by_values_from_variables(  # noqa: E501
    schema_with_costs,
):
    query = """
        fragment child on Child {
          online
        }
        query testQuery($value: Int!) {
          child(value: $value) {
            ...child
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"value": 5})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_child_fragment_cost_defined_in_directive_is_multiplied_by_values_from_literal(
    schema_with_costs,
):
    query = """
        fragment child on Child {
          online
        }
        {
          child(value: 5) {
            ...child
          }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 3. Actual cost is 20",
            extensions={"cost": {"requestedQueryCost": 20, "maximumAvailable": 3}},
        )
    ]


def test_same_fragment_spread_under_different_multipliers_is_costed_per_context(
    schema_with_costs,
):
    query = """
        fragment frag on Child {
          online
        }
        {
          a: child(value: 3) { ...frag }
          b: child(value: 7) { ...frag }
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=1)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 1. Actual cost is 40",
            extensions={"cost": {"requestedQueryCost": 40, "maximumAvailable": 1}},
        )
    ]


def _count_compute_node_cost_calls(monkeypatch):
    original_compute_node_cost = CostValidator.compute_node_cost
    call_count = 0

    def counting_compute_node_cost(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_compute_node_cost(self, *args, **kwargs)

    monkeypatch.setattr(CostValidator, "compute_node_cost", counting_compute_node_cost)
    return lambda: call_count


def test_fragment_dag_with_differently_multiplied_branches_does_not_cause_exponential_recursion(  # noqa: E501
    monkeypatch,
):
    cost_directive = """
        directive @cost(
            complexity: Int, multipliers: [String!], useMultipliers: Boolean
        ) on FIELD | FIELD_DEFINITION
    """
    type_defs = """
        type Query {
          start: Node
        }
        type Node {
          a(value: Int!): Node @cost(complexity: 1, multipliers: ["value"])
          b(value: Int!): Node @cost(complexity: 1, multipliers: ["value"])
          leaf: Int!
        }
    """
    schema = make_executable_schema([type_defs, cost_directive])

    depth = 25
    lines = ["query { start { ...F0 } }"]
    for index in range(depth):
        if index + 1 < depth:
            selection = (
                f"x: a(value: 2) {{ ...F{index + 1} }} "
                f"y: b(value: 3) {{ ...F{index + 1} }}"
            )
        else:
            selection = "leaf"
        lines.append(f"fragment F{index} on Node {{ {selection} }}")
    query = "\n".join(lines)

    ast = parse(query)
    rule = cost_validator(maximum_cost=10**100)

    get_call_count = _count_compute_node_cost_calls(monkeypatch)
    result = validate(schema, ast, [rule])

    assert result == []
    assert get_call_count() <= depth * 10


def test_cost_directive_multiplier_counts_list_argument_length() -> None:
    # A list-valued multiplier argument must contribute its length, otherwise a
    # large list bypasses the maximum-cost guard entirely (the field's cost
    # collapses to its complexity). Regression test for the dropped list
    # multiplier in CostValidator.get_multipliers_from_string.
    type_defs = """
        type Query {
            things(ids: [ID!]!): Int! @cost(complexity: 1, multipliers: ["ids"])
        }
    """
    schema = make_executable_schema([type_defs, cost_directive])
    ast = parse('{ things(ids: ["a", "b", "c", "d", "e"]) }')

    # cost = complexity(1) * len(ids)=5
    rejected = validate(schema, ast, [cost_validator(maximum_cost=4)])
    assert rejected == [
        GraphQLError(
            "The query exceeds the maximum cost of 4. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 4}},
        )
    ]
    assert validate(schema, ast, [cost_validator(maximum_cost=5)]) == []


def test_cost_map_multiplier_counts_list_argument_length() -> None:
    type_defs = """
        type Query {
            things(ids: [ID!]!): Int!
        }
    """
    schema = make_executable_schema(type_defs)
    ast = parse('{ things(ids: ["a", "b", "c", "d", "e"]) }')
    rule = cost_validator(
        maximum_cost=4,
        cost_map={"Query": {"things": {"complexity": 1, "multipliers": ["ids"]}}},
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError(
            "The query exceeds the maximum cost of 4. Actual cost is 5",
            extensions={"cost": {"requestedQueryCost": 5, "maximumAvailable": 4}},
        )
    ]


def test_cost_directive_multiplier_ignores_non_numeric_argument() -> None:
    # A multiplier naming a scalar argument that isn't a number contributes
    # nothing, so the field costs just its complexity.
    type_defs = """
        type Query {
            things(label: String!): Int! @cost(complexity: 3, multipliers: ["label"])
        }
    """
    schema = make_executable_schema([type_defs, cost_directive])
    ast = parse('{ things(label: "abc") }')

    assert validate(schema, ast, [cost_validator(maximum_cost=3)]) == []
    assert validate(schema, ast, [cost_validator(maximum_cost=2)]) == [
        GraphQLError(
            "The query exceeds the maximum cost of 2. Actual cost is 3",
            extensions={"cost": {"requestedQueryCost": 3, "maximumAvailable": 2}},
        )
    ]
