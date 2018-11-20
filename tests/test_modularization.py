from unittest.mock import Mock

import pytest
from graphql import graphql_sync

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

duplicate_typedef = """
    type User {
        firstName: String
    }
"""

resolvers = {"Query": {"user": lambda *_: {"username": "Bob"}}}

overriding_resolvers = {"Query": {"user": lambda *_: {"firstName": "Bob"}}}


def test_list_of_typedefs_is_merged():
    type_defs = [root_typedef, module_typedef]
    schema = make_executable_schema(type_defs, resolvers)

    result = graphql_sync(schema, "{ user { username } }")
    assert result.errors is None
    assert result.data == {"user": {"username": "Bob"}}


def test_redefining_existing_type_causes_type_error():
    type_defs = [root_typedef, module_typedef, duplicate_typedef]
    with pytest.raises(TypeError):
        make_executable_schema(type_defs, overriding_resolvers)


def test_list_of_resolvers_maps_is_merged():
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

    result = graphql_sync(schema, "{ user { firstName } }")
    assert result.errors is None
    assert result.data == {"user": {"firstName": "Joe"}}

    result = graphql_sync(schema, "{ test(data: { value: 4 }) }")
    assert result.errors is None
    assert result.data == {"test": 42}
