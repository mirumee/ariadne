
from graphql import graphql
from graphql.utils.introspection_query import introspection_query

from ariadne import make_executable_schema

type_defs = """
    type Query {
        test: String
        user(id: Int!): User
        users: [User!]!
    }

    type User {
        name: String
        age: Int!
    }
"""


def test_schema_introspection_query_has_no_errors():
    schema = make_executable_schema(type_defs, {})
    result = graphql(schema, introspection_query)
    assert result.errors is None
