import pytest
from graphql import GraphQLError
from graphql.language import parse
from graphql.validation import validate

from ariadne import make_executable_schema
from ariadne.validation import cost_validator

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
