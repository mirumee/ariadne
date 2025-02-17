from unittest.mock import Mock

import pytest
from graphql import build_schema, graphql_sync

from ariadne import InterfaceType, ObjectType, QueryType, make_executable_schema

type_defs = """
    type Query {
        result: SearchResult
        user: User!
        thread: Thread!
    }

    type User implements SearchResult {
        username: String!
        summary: String!
    }

    type Thread implements SearchResult {
        title: String!
        summary: String!
    }

    type Post {
        summary: String!
    }

    interface SearchResult {
        summary: String!
    }
"""


@pytest.fixture
def schema():
    return build_schema(type_defs)


def test_attempt_to_bind_interface_to_undefined_type_raises_error(schema):
    interface = InterfaceType("Test")
    with pytest.raises(ValueError):
        interface.bind_to_schema(schema)


def test_attempt_to_bind_interface_to_invalid_type_raises_error(schema):
    interface = InterfaceType("Query")
    with pytest.raises(ValueError):
        interface.bind_to_schema(schema)


test_query = """
    {
        result {
            __typename
            ... on User {
                username
                summary
            }
            ... on Thread {
                title
                summary
            }
        }
    }
"""

User = Mock(username="User", summary="User Summary")
Thread = Mock(title="Thread", summary="Thread Summary")


@pytest.fixture
def query():
    return QueryType()


@pytest.fixture
def query_with_user_result(query):
    query.set_field("result", lambda *_: User)
    return query


@pytest.fixture
def query_with_thread_result(query):
    query.set_field("result", lambda *_: Thread)
    return query


@pytest.fixture
def query_with_invalid_result(query):
    query.set_field("result", lambda *_: True)
    return query


def test_interface_type_resolver_may_be_set_on_initialization(query_with_user_result):
    interface = InterfaceType("SearchResult", type_resolver=lambda *_: "User")
    schema = make_executable_schema(type_defs, [query_with_user_result, interface])
    result = graphql_sync(schema, "{ result { __typename } }")
    assert result.data == {"result": {"__typename": "User"}}


def test_interface_type_resolver_may_be_set_using_setter(query_with_user_result):
    def resolve_result_type(*_):
        return "User"

    interface = InterfaceType("SearchResult")
    interface.set_type_resolver(resolve_result_type)

    schema = make_executable_schema(type_defs, [query_with_user_result, interface])
    result = graphql_sync(schema, "{ result { __typename } }")
    assert result.data == {"result": {"__typename": "User"}}


def test_interface_type_resolver_may_be_set_using_decorator(query_with_user_result):
    interface = InterfaceType("SearchResult")

    @interface.type_resolver
    def resolve_result_type(*_):
        return "User"

    schema = make_executable_schema(type_defs, [query_with_user_result, interface])
    result = graphql_sync(schema, "{ result { __typename } }")
    assert result.data == {"result": {"__typename": "User"}}


def resolve_result_type(obj, *_):
    if obj == User:
        return "User"
    if obj == Thread:
        return "Thread"
    return None


@pytest.fixture
def interface():
    return InterfaceType("SearchResult", type_resolver=resolve_result_type)


def test_result_is_username_if_interface_resolves_type_to_user(
    query_with_user_result, interface
):
    schema = make_executable_schema(type_defs, [query_with_user_result, interface])
    result = graphql_sync(schema, test_query)
    assert result.data == {
        "result": {
            "__typename": "User",
            "username": User.username,
            "summary": User.summary,
        }
    }


def test_result_is_thread_title_if_interface_resolves_type_to_thread(
    query_with_thread_result, interface
):
    schema = make_executable_schema(type_defs, [query_with_thread_result, interface])
    result = graphql_sync(schema, test_query)
    assert result.data == {
        "result": {
            "__typename": "Thread",
            "title": Thread.title,
            "summary": Thread.summary,
        }
    }


def test_query_errors_if_interface_didnt_resolve_the_type(
    query_with_invalid_result, interface
):
    schema = make_executable_schema(type_defs, [query_with_invalid_result, interface])
    result = graphql_sync(schema, test_query)
    assert result.data == {"result": None}


def test_attempt_bind_interface_field_to_undefined_field_raises_error(
    schema, interface
):
    interface.set_alias("score", "_")
    with pytest.raises(ValueError):
        interface.bind_to_schema(schema)


def test_resolver(*_):
    pass


def test_field_decorator_assigns_decorated_function_as_field_resolver(
    schema, query_with_user_result, interface
):
    interface.field("summary")(test_resolver)
    interface.bind_to_schema(schema)
    query_with_user_result.bind_to_schema(schema)

    field = schema.type_map.get(interface.name).fields["summary"]
    assert field.resolve is test_resolver


def test_set_field_method_assigns_function_as_field_resolver(
    schema, query_with_user_result, interface
):
    interface.set_field("summary", test_resolver)
    interface.bind_to_schema(schema)
    query_with_user_result.bind_to_schema(schema)

    field = schema.type_map.get(interface.name).fields["summary"]
    assert field.resolve is test_resolver


def test_alias_method_creates_resolver_for_specified_attribute(
    schema, query_with_user_result, interface
):
    interface.set_alias("summary", "username")
    interface.bind_to_schema(schema)
    query_with_user_result.bind_to_schema(schema)

    field = schema.type_map.get(interface.name).fields["summary"]
    assert field.resolve


def test_interface_doesnt_set_resolver_for_type_not_implementing_it(schema, interface):
    interface.set_field("summary", lambda *_: "Summary")
    interface.bind_to_schema(schema)

    field = schema.type_map.get("Post").fields["summary"]
    assert field.resolve is None


def test_interface_sets_resolver_on_implementing_types(schema, interface):
    interface.set_field("summary", test_resolver)
    interface.bind_to_schema(schema)

    user_field = schema.type_map.get("User").fields["summary"]
    assert user_field.resolve is test_resolver
    thread_field = schema.type_map.get("Thread").fields["summary"]
    assert thread_field.resolve is test_resolver


def test_interface_resolver_doesnt_override_existing_resolver(schema, interface):
    user = ObjectType("User")
    user.set_field("summary", test_resolver)
    user.bind_to_schema(schema)

    def interface_resolver(*_):
        pass  # pragma: no cover

    interface.set_field("summary", interface_resolver)
    interface.bind_to_schema(schema)

    field = schema.type_map.get("User").fields["summary"]
    assert field.resolve is test_resolver
