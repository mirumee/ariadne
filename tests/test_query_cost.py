from graphql import GraphQLError
from graphql.language import parse
from graphql.validation import validate

from ariadne.executable_schema import make_executable_schema
from ariadne.query_cost import cost_validator


def test_query_cost_with_cost_map():
    type_defs = """
    type Query {
        alpha: String!
        charlie(first: Int): [Charlie!]!
    }

    type Charlie {
        delta: Delta!
    }

    type Delta {
        echo: String!
    }
    """

    query = """
    query Q($page: Int!) {
        alpha
        bravo: alpha
        charlie(first: $page) {
            delta {
                echo
            }
        }
    }
    """
    schema = make_executable_schema(type_defs, {})
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=10,
        variables={"page": 5},
        cost_map={
            "Query": {
                "alpha": {"complexity": 1},
                "charlie": {"complexity": 5, "multipliers": ["first"]},
            },
            "Charlie": {"delta": {"complexity": 2}},
            "Delta": {"echo": {"complexity": 1}},
        },
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 10. Actual cost is 42")
    ]


def test_query_cost_with_directives():
    type_defs = """
    directive @cost(complexity: Int, multipliers: [String!], useMultipliers: Boolean) on FIELD | FIELD_DEFINITION

    type Query {
        alpha: String! @cost(complexity: 1)
        charlie(first: Int): [Charlie!]! @cost(complexity: 5, multipliers: ["first"])
    }

    type Charlie {
        delta: Delta! @cost(complexity: 2)
    }

    type Delta {
        echo: String! @cost(complexity: 1)
    }
    """

    query = """
    query Q($page: Int!) {
        alpha
        bravo: alpha
        charlie(first: $page) {
            delta {
                echo
            }
        }
    }
    """
    schema = make_executable_schema(type_defs, {})
    ast = parse(query)
    rule = cost_validator(
        maximum_cost=10,
        variables={"page": 5},
    )
    result = validate(schema, ast, [rule])
    assert result == [
        GraphQLError("The query exceeds the maximum cost of 10. Actual cost is 42")
    ]
