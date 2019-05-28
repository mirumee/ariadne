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
            simple(limit: Int!): Int!
            complex(min: Int!, max: Int!): Int!
            deep(limit: Int!): [Child!]!
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
            simple(limit: Int!): Int! @cost(complexity: 1, multipliers: ["limit"])
            complex(min: Int!, max: Int!): Int! @cost(complexity: 1, multipliers: ["min", "max"])
            deep(limit: Int!): [Child!]! @cost(complexity: 1, multipliers: ["limit"])
        }

        type Child {
            name: String!
            online: Boolean! @cost(complexity: 1)
        }
    """

    return make_executable_schema([type_defs, cost_directive])


cost_map = {
    "Query": {
        "constant": {"complexity": 3},
        "simple": {"complexity": 1, "multipliers": ["limit"]},
        "complex": {"complexity": 1, "multipliers": ["min", "max"]},
        "deep": {"complexity": 1, "multipliers": ["limit"]},
    },
    "Child": {"constant": {"complexity": 1}},
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


def test_field_cost_defined_in_map_is_multiplied_by_value_from_variables():
    type_defs = """
        type Query {
            test(value: Int!): String!
        }
    """

    query = """
        query testQuery($value: Int!) {
            test(value: $value)
        }
    """
    schema = make_executable_schema(type_defs)
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=10,
        variables={"value": 5},
        cost_map={"Query": {"test": {"complexity": 5, "multipliers": ["value"]}}},
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 10. Actual cost is 25")
    ]


def test_field_cost_defined_in_map_is_multiplied_by_value_from_literal():
    type_defs = """
        type Query {
            test(value: Int!): String!
        }
    """

    query = "{ test(value: 5) }"
    schema = make_executable_schema(type_defs)
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=10,
        cost_map={"Query": {"test": {"complexity": 5, "multipliers": ["value"]}}},
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 10. Actual cost is 25")
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_value_from_variables():
    type_defs = """
        directive @cost(complexity: Int, multipliers: [String!], useMultipliers: Boolean) on FIELD | FIELD_DEFINITION

        type Query {
            test(value: Int!): String! @cost(complexity: 5, multipliers: ["value"])
        }
    """

    query = """
        query testQuery($value: Int!) {
            test(value: $value)
        }
    """
    schema = make_executable_schema(type_defs)
    ast = parse(query)
    rule = cost_validator(maximum_cost=10, variables={"value": 5})
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 10. Actual cost is 25")
    ]


def test_field_cost_defined_in_directive_is_multiplied_by_value_from_literal():
    type_defs = """
        type Query {
            test(value: Int!): String! @cost(complexity: 5, multipliers: ["value"])
        }
    """

    query = "{ test(value: 5) }"
    schema = make_executable_schema([type_defs, cost_directive])
    ast = parse(query)
    rule = cost_validator(maximum_cost=10, variables={"value": 5})
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 10. Actual cost is 25")
    ]
