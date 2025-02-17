import pytest
from graphql import build_schema, graphql_sync

from ariadne import ObjectType


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


def test_attempt_bind_object_type_to_undefined_type_raises_error(schema):
    query = ObjectType("Test")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_attempt_bind_object_type_to_invalid_type_raises_error(schema):
    query = ObjectType("Date")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_attempt_bind_object_type_field_to_undefined_field_raises_error(schema):
    query = ObjectType("Query")
    query.set_alias("user", "_")
    with pytest.raises(ValueError):
        query.bind_to_schema(schema)


def test_field_resolver_can_be_set_using_decorator(schema):
    query = ObjectType("Query")
    query.field("hello")(lambda *_: "World")
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "World"}


def test_value_error_is_raised_if_field_decorator_was_used_without_argument():
    query = ObjectType("Query")
    with pytest.raises(ValueError):
        query.field(lambda *_: "World")


def test_field_resolver_can_be_set_using_setter(schema):
    query = ObjectType("Query")
    query.set_field("hello", lambda *_: "World")
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "World"}


def test_set_alias_method_creates_resolver_for_specified_attribute(schema):
    query = ObjectType("Query")
    query.set_alias("hello", "test")
    query.bind_to_schema(schema)

    result = graphql_sync(schema, "{ hello }", root_value={"test": "World"})
    assert result.errors is None
    assert result.data == {"hello": "World"}
