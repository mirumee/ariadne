from graphql import graphql

from ariadne import make_executable_schema

root_typedefs = """
    type Query {
        user: User
    }
"""

module_typedefs = """
    type User {
        username: String
    }
"""

resolvers = {"Query": {"user": lambda *_: {"username": "Bob"}}}


def test_modularize_typedefs():
    type_defs = [root_typedefs, module_typedefs]
    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ user { username} }")
    assert result.errors is None
    assert result.data == {"user": {"username": "Bob"}}
