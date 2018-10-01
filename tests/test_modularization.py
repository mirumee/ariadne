from unittest.mock import Mock

from graphql import graphql

from ariadne import make_executable_schema, resolve_to

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


def test_accept_list_of_resolvers_maps():
    type_defs = """
        type Query {
            user: User
            test(data: TestInput): Int
        }

        type User {
            firstName: String
        }

        input TestInput {
            value: Int
        }
    """

    def resolve_test(*_, data):
        assert data == {"value": 4}
        return "42"

    resolvers = [
        {
            "Query": {"user": lambda *_: Mock(first_name="Joe")},
            "User": {"firstName": resolve_to("first_name")},
        },
        {"Query": {"test": resolve_test}},
    ]

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ user { firstName } }")
    assert result.errors is None
    assert result.data == {"user": {"firstName": "Joe"}}

    result = graphql(schema, "{ test(data: { value: 4 }) }")
    assert result.errors is None
    assert result.data == {"test": 42}
