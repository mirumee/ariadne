from graphql import graphql

from ariadne import make_executable_schema

root_typedef = """
    type Query {
        user: User
    }
"""

module_typedef = """
    type User {
        username: String
    }
"""

overriding_typedef = """
    type User {
        firstName: String
    }
"""

resolvers = {"Query": {"user": lambda *_: {"username": "Bob"}}}

overriding_resolvers = {"Query": {"user": lambda *_: {"firstName": "Bob"}}}


def test_concat_typedefs():
    type_defs = [root_typedef, module_typedef]
    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ user { username } }")
    assert result.errors is None
    assert result.data == {"user": {"username": "Bob"}}


def test_override_typedef():
    type_defs = [root_typedef, module_typedef, overriding_typedef]
    schema = make_executable_schema(type_defs, overriding_resolvers)

    result = graphql(schema, "{ user { firstName } }")
    assert result.errors is None
    assert result.data == {"user": {"firstName": "Bob"}}


def test_override_typedef_outdated_field():
    type_defs = [root_typedef, module_typedef, overriding_typedef]
    schema = make_executable_schema(type_defs, overriding_resolvers)

    result = graphql(schema, "{ user { username } }")
    assert result.errors is not None
    assert str(result.errors[0]) == 'Cannot query field "username" on type "User".'
    assert result.data is None
