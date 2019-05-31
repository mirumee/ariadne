import pytest

from graphql import GraphQLError
from graphql.language import parse
from graphql.validation import validate

from ariadne.executable_schema import make_executable_schema
from ariadne.validation.query_cost import cost_validator

cost_directive = """
directive @cost(complexity: Int, multipliers: [String!], useMultipliers: Boolean) on FIELD | FIELD_DEFINITION
"""


@pytest.fixture
def schema():
    type_defs = """
        type Query {
            constant: Int!
            simple(value: Int!): Int!
            complex(valueA: Int!, valueB: Int!): Int!
            child(value: Int!): [Child!]!
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
            complex(valueA: Int!, valueB: Int!): Int! @cost(complexity: 1, multipliers: ["valueA", "valueB"])
            child(value: Int!): [Child!]! @cost(complexity: 1, multipliers: ["value"])
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
        "child": {"complexity": 1, "multipliers": ["value"]},
    },
    "Child": {"online": {"complexity": 3}},
}


def test_cost_map_is_used_to_calculate_query_cost(schema):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 1. Actual cost is 3")
    ]


def test_cost_directive_is_used_to_calculate_query_cost(schema_with_costs):
    ast = parse("{ constant }")
    rule = cost_validator(maximum_cost=1)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 1. Actual cost is 3")
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
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 5")
    ]


def test_field_cost_defined_in_map_is_multiplied_by_value_from_literal(schema):
    query = "{ simple(value: 5) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 5")
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_value_from_variables(
    schema_with_costs
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
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 5")
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_value_from_literal(
    schema_with_costs
):
    query = "{ simple(value: 5) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 5")
    ]


def test_complex_field_cost_defined_in_map_is_multiplied_by_values_from_variables(
    schema
):
    query = """
        query testQuery($valueA: Int!, $valueB: Int!) {
            complex(valueA: $valueA, valueB: $valueB)
        }
    """
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=3, variables={"valueA": 5, "valueB": 6}, cost_map=cost_map
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 11")
    ]


def test_complex_field_cost_defined_in_map_is_multiplied_by_values_from_literal(schema):
    query = "{ complex(valueA: 5, valueB: 6) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 11")
    ]


def test_complex_field_cost_defined_in_directive_is_multiplied_by_values_from_variables(
    schema_with_costs
):
    query = """
        query testQuery($valueA: Int!, $valueB: Int!) {
            complex(valueA: $valueA, valueB: $valueB)
        }
    """
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, variables={"valueA": 5, "valueB": 6})
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 11")
    ]


def test_complex_field_cost_defined_in_directive_is_multiplied_by_values_from_literal(
    schema_with_costs
):
    query = "{ complex(valueA: 5, valueB: 6) }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 11")
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
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 20")
    ]


def test_child_field_cost_defined_in_map_is_multiplied_by_values_from_literal(schema):
    query = "{ child(value: 5) { name online } }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3, cost_map=cost_map)
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 20")
    ]


def test_child_field_cost_defined_in_directive_is_multiplied_by_values_from_variables(
    schema_with_costs
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
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 20")
    ]


def test_child_field_cost_defined_in_directive_is_multiplied_by_values_from_literal(
    schema_with_costs
):
    query = "{ child(value: 5) { name online } }"
    ast = parse(query)
    rule = cost_validator(maximum_cost=3)
    result = validate(schema_with_costs, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 3. Actual cost is 20")
    ]
