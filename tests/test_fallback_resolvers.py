import pytest
from graphql import graphql_sync, build_schema

from ariadne import ResolverMap, fallback_resolvers, snake_case_fallback_resolvers


@pytest.fixture
def schema():
    return build_schema(
        """
            type Query {
                hello: Boolean
                snake_case: Boolean
                Camel: Boolean
                pascalCase: Boolean
            }
        """
    )


query = "{ hello snake_case Camel pascalCase }"


def test_default_fallback_resolves_fields_by_exact_names(schema):
    fallback_resolvers.bind_to_schema(schema)
    query_root = {"hello": True, "snake_case": True, "Camel": True, "pascalCase": True}
    result = graphql_sync(schema, query, root_value=query_root)
    assert result.data == query_root


def test_default_fallback_is_not_converting_field_name_case_to_snake_case(schema):
    fallback_resolvers.bind_to_schema(schema)
    query_root = {"hello": True, "snake_case": True, "camel": True, "pascal_case": True}
    result = graphql_sync(schema, query, root_value=query_root)
    assert result.data == {
        "hello": True,
        "snake_case": True,
        "Camel": None,
        "pascalCase": None,
    }


def test_default_fallback_is_not_replacing_already_set_resolvers(schema):
    resolvers_map = ResolverMap("Query")
    resolvers_map.field("hello", resolver=lambda *_: False)
    resolvers_map.field("snake_case", resolver=lambda *_: False)
    resolvers_map.bind_to_schema(schema)
    fallback_resolvers.bind_to_schema(schema)
    query_root = {"hello": True, "snake_case": True, "camel": True, "pascal_case": True}
    result = graphql_sync(schema, query, root_value=query_root)
    assert result.data == {
        "hello": False,
        "snake_case": False,
        "Camel": None,
        "pascalCase": None,
    }


def test_snake_case_fallback_resolves_fields_names_to_snake_case_counterparts(schema):
    snake_case_fallback_resolvers.bind_to_schema(schema)
    query_root = {"hello": True, "snake_case": True, "camel": True, "pascal_case": True}
    result = graphql_sync(schema, query, root_value=query_root)
    assert result.data == {
        "hello": True,
        "snake_case": True,
        "Camel": True,
        "pascalCase": True,
    }


def test_snake_case_fallback_is_not_resolving_fields_by_exact_names(schema):
    snake_case_fallback_resolvers.bind_to_schema(schema)
    query_root = {"hello": True, "snake_case": True, "Camel": True, "pascalCase": True}
    result = graphql_sync(schema, query, root_value=query_root)
    assert result.data == {
        "hello": True,
        "snake_case": True,
        "Camel": None,
        "pascalCase": None,
    }


def test_snake_case_fallback_is_not_replacing_already_set_resolvers(schema):
    resolvers_map = ResolverMap("Query")
    resolvers_map.field("hello", resolver=lambda *_: False)
    resolvers_map.field("Camel", resolver=lambda *_: False)
    resolvers_map.bind_to_schema(schema)
    snake_case_fallback_resolvers.bind_to_schema(schema)
    query_root = {"hello": True, "snake_case": True, "camel": True, "pascal_case": True}
    result = graphql_sync(schema, query, root_value=query_root)
    assert result.data == {
        "hello": False,
        "snake_case": True,
        "Camel": False,
        "pascalCase": True,
    }
