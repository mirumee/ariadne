from graphql import get_introspection_query, graphql_sync

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
        dateOfBirth: Date!
    }

    scalar Date
"""


def test_executable_schema_can_be_introspected():
    schema = make_executable_schema(type_defs)
    introspection_query = get_introspection_query(descriptions=True)
    result = graphql_sync(schema, introspection_query)
    assert result.errors is None
    assert result.data is not None
    assert "__schema" in result.data
    type_names = [
        schema_type["name"] for schema_type in result.data["__schema"]["types"]
    ]
    assert "User" in type_names
    assert "Query" in type_names
    assert "Date" in type_names
