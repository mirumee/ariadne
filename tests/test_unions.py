from unittest.mock import Mock

import pytest
from graphql import build_schema, graphql_sync

from ariadne import QueryType, UnionType, make_executable_schema

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


def test_attempt_to_bind_union_to_undefined_type_raises_error(schema):
    union = UnionType("Test")
    with pytest.raises(ValueError):
        union.bind_to_schema(schema)


def test_attempt_to_bind_union_to_invalid_type_raises_error(schema):
    union = UnionType("Query")
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

User = Mock(username="User")
Thread = Mock(title="Thread")


@pytest.fixture
def query():
    return QueryType()


@pytest.fixture
def query_with_user_item(query):
    query.set_field("item", lambda *_: User)
    return query


@pytest.fixture
def query_with_thread_item(query):
    query.set_field("item", lambda *_: Thread)
    return query


@pytest.fixture
def query_with_invalid_item(query):
    query.set_field("item", lambda *_: True)
    return query


def test_union_type_resolver_may_be_set_on_initialization(query_with_user_item):
    union = UnionType("FeedItem", type_resolver=lambda *_: "User")
    schema = make_executable_schema(type_defs, [query_with_user_item, union])
    result = graphql_sync(schema, "{ item { __typename } }")
    assert result.data == {"item": {"__typename": "User"}}


def test_union_type_resolver_may_be_set_using_setter(query_with_user_item):
    def resolve_result_type(*_):
        return "User"

    union = UnionType("FeedItem")
    union.set_type_resolver(resolve_result_type)

    schema = make_executable_schema(type_defs, [query_with_user_item, union])
    result = graphql_sync(schema, "{ item { __typename } }")
    assert result.data == {"item": {"__typename": "User"}}


def test_union_type_resolver_may_be_set_using_decorator(query_with_user_item):
    union = UnionType("FeedItem")

    @union.type_resolver
    def resolve_result_type(*_):
        return "User"

    schema = make_executable_schema(type_defs, [query_with_user_item, union])
    result = graphql_sync(schema, "{ item { __typename } }")
    assert result.data == {"item": {"__typename": "User"}}


def resolve_result_type(obj, *_):
    if obj == User:
        return "User"
    if obj == Thread:
        return "Thread"
    return None


def test_result_is_username_if_union_resolves_type_to_user(query_with_user_item):
    union = UnionType("FeedItem", type_resolver=resolve_result_type)
    schema = make_executable_schema(type_defs, [query_with_user_item, union])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": {"__typename": "User", "username": User.username}}


def test_result_is_thread_title_if_union_resolves_type_to_thread(
    query_with_thread_item,
):
    union = UnionType("FeedItem", type_resolver=resolve_result_type)
    schema = make_executable_schema(type_defs, [query_with_thread_item, union])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": {"__typename": "Thread", "title": Thread.title}}


def test_result_is_none_if_union_didnt_resolve_the_type(query_with_invalid_item):
    union = UnionType("FeedItem", type_resolver=resolve_result_type)
    schema = make_executable_schema(type_defs, [query_with_invalid_item, union])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": None}
