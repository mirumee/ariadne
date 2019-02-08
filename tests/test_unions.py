from unittest.mock import Mock

import pytest
from graphql import build_schema, graphql_sync

from ariadne import ResolverMap, Union, make_executable_schema

type_defs = """
    union FeedItem = User | Thread

    type User {
        username: String
    }

    type Thread {
        title: String
    }

    type Query {
        item: FeedItem
    }
"""


@pytest.fixture
def schema():
    return build_schema(type_defs)


def test_attempt_bind_union_to_undefined_type_raises_error(schema):
    union = Union("Test")
    with pytest.raises(ValueError):
        union.bind_to_schema(schema)


def test_attempt_bind_union_to_invalid_type_raises_error(schema):
    union = Union("Query")
    with pytest.raises(ValueError):
        union.bind_to_schema(schema)


test_query = """
    {
        item {
            __typename
            ... on User {
                username
            }
            ... on Thread {
                title
            }
        }
    }
"""

user = Mock(username="User")
thread = Mock(title="Thread")


def test_union_type_resolver_may_be_set_on_initialization():
    query = ResolverMap("Query")
    query.field(  # pylint: disable=unexpected-keyword-arg
        "item", resolver=lambda *_: user
    )

    union = Union("FeedItem", type_resolver=lambda *_: "User")
    schema = make_executable_schema(type_defs, [query, union])

    result = graphql_sync(schema, "{ item { __typename } }")
    assert result.data == {"item": {"__typename": "User"}}


def test_union_type_resolver_may_be_set_using_decorator():
    query = ResolverMap("Query")
    query.field(  # pylint: disable=unexpected-keyword-arg
        "item", resolver=lambda *_: user
    )

    union = Union("FeedItem")

    @union.type_resolver
    def resolve_result_type(*_):  # pylint: disable=unused-variable
        return "User"

    schema = make_executable_schema(type_defs, [query, union])

    result = graphql_sync(schema, "{ item { __typename } }")
    assert result.data == {"item": {"__typename": "User"}}


def resolve_result_type(obj, *_):
    if obj == user:
        return "User"
    if obj == thread:
        return "Thread"
    return None


def test_result_is_username_if_union_resolves_type_to_user():
    query = ResolverMap("Query")
    query.field(  # pylint: disable=unexpected-keyword-arg
        "item", resolver=lambda *_: user
    )
    union = Union("FeedItem", type_resolver=resolve_result_type)

    schema = make_executable_schema(type_defs, [query, union])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": {"__typename": "User", "username": user.username}}


def test_result_is_thread_title_if_union_resolves_type_to_thread():
    query = ResolverMap("Query")
    query.field(  # pylint: disable=unexpected-keyword-arg
        "item", resolver=lambda *_: thread
    )
    union = Union("FeedItem", type_resolver=resolve_result_type)

    schema = make_executable_schema(type_defs, [query, union])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": {"__typename": "Thread", "title": thread.title}}


def test_result_is_none_if_union_didnt_resolve_the_type():
    query = ResolverMap("Query")
    query.field(  # pylint: disable=unexpected-keyword-arg
        "item", resolver=lambda *_: True
    )
    union = Union("FeedItem", type_resolver=resolve_result_type)

    schema = make_executable_schema(type_defs, [query, union])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": None}
