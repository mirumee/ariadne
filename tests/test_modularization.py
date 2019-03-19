from unittest.mock import Mock

import pytest
from graphql import graphql_sync

from ariadne import ObjectType, make_executable_schema

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


def test_list_of_type_defs_is_merged_into_executable_schema():
    query = ObjectType("Query")
    query.set_field("user", lambda *_: {"username": "Bob"})

    type_defs = [root_typedef, module_typedef]
    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ user { username } }")
    assert result.errors is None
    assert result.data == {"user": {"username": "Bob"}}


def test_redefining_existing_type_causes_type_error():
    type_defs = [root_typedef, module_typedef, duplicate_typedef]
    with pytest.raises(TypeError):
        make_executable_schema(type_defs)


def test_same_type_resolver_maps_are_merged_into_executable_schema():
    type_defs = """
        type Query {
            hello: String
            test(data: Int): Boolean
        }
    """

    query = ObjectType("Query")
    query.set_field("hello", lambda *_: "World!")

    extending_query = ObjectType("Query")

    @extending_query.field("test")
    def resolve_test(*_, data):  # pylint: disable=unused-variable
        assert data == 4
        return True

    schema = make_executable_schema(type_defs, [query, extending_query])

    result = graphql_sync(schema, "{ hello test(data: 4) }")
    assert result.errors is None
    assert result.data == {"hello": "World!", "test": True}


def test_different_types_resolver_maps_are_merged_into_executable_schema():
    type_defs = """
        type Query {
            user: User
        }

        type User {
            username: String
        }
    """

    query = ObjectType("Query")
    query.set_field("user", lambda *_: Mock(first_name="Joe"))

    user = ObjectType("User")
    user.set_alias("username", "first_name")

    schema = make_executable_schema(type_defs, [query, user])

    result = graphql_sync(schema, "{ user { username } }")
    assert result.errors is None
    assert result.data == {"user": {"username": "Joe"}}
