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


def test_if_type_is_not_defined_in_schema_value_error_is_raised(schema):
    query = ResolverMap("Test")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_if_type_is_defined_in_schema_but_is_incorrect_value_error_is_raised(schema):
    query = ResolverMap("Date")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_if_type_field_is_not_defined_in_schema_value_error_is_raised(schema):
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


def test_alias_method_creates_resolver_for_specified_attribute(schema):
    query = ResolverMap("Query")
    query.alias("hello", "test")
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }", root_value={"test": "World"})
    assert result.errors is None
    assert result.data == {"hello": "World"}
