import pytest
from graphql import graphql_sync, build_schema

from ariadne import ResolverMap


@pytest.fixture
def schema():
    return build_schema(
        """
            type Query {
                hello: String
            }

            scalar Date
        """
    )


def test_attempt_bind_resolver_map_to_undefined_type_raises_error(schema):
    query = ResolverMap("Test")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_attempt_bind_resolver_map_to_invalid_type_raises_error(schema):
    query = ResolverMap("Date")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_attempt_bind_resolver_map_field_to_undefined_field_raises_error(schema):
    query = ResolverMap("Query")
    query.alias("user", "_")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_field_method_assigns_decorated_function_as_field_resolver(schema):
    query = ResolverMap("Query")
    query.field("hello")(lambda *_: "World")
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "World"}


def test_field_method_assigns_function_as_field_resolver(schema):
    query = ResolverMap("Query")
    query.field(  # pylint: disable=unexpected-keyword-arg
        "hello", resolver=lambda *_: "World"
    )
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "World"}


def test_alias_method_creates_resolver_for_specified_attribute(schema):
    query = ResolverMap("Query")
    query.alias("hello", "test")
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }", root_value={"test": "World"})
    assert result.errors is None
    assert result.data == {"hello": "World"}
