from unittest.mock import Mock

from graphql import graphql_sync

from ariadne import ObjectType, QueryType, make_executable_schema


def test_default_resolver_resolves_value_from_dict_item():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
        }
    """

    query = QueryType()
    query.set_field("test", lambda *_: {"node": "custom"})

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test { node } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "custom"}}


def test_default_resolver_resolves_value_from_object_attr():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
        }
    """

    query = QueryType()
    query.set_field("test", lambda *_: Mock(node="custom"))

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test { node } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "custom"}}


def test_custom_resolver_is_called_to_resolve_custom_type_field_value():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
        }
    """

    query = QueryType()
    query.set_field("test", lambda *_: {"node": "custom"})

    custom = ObjectType("Custom")
    custom.set_field("node", lambda *_: "deep")

    schema = make_executable_schema(type_defs, [query, custom])

    result = graphql_sync(schema, "{ test { node } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "deep"}}


def test_custom_and_default_resolvers_are_combined_to_resolve_custom_type_fields():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
            default: String
        }
    """

    query = QueryType()
    query.set_field("test", lambda *_: {"node": "custom", "default": "ok"})

    custom = ObjectType("Custom")
    custom.set_field("node", lambda *_: "deep")

    schema = make_executable_schema(type_defs, [query, custom])

    result = graphql_sync(schema, "{ test { node default } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "deep", "default": "ok"}}


def test_custom_resolver_is_called_with_arguments_passed_with_query():
    type_defs = """
        type Query {
            test(returnValue: Int!): Int
        }
    """

    query = QueryType()

    @query.field("test")
    def resolve_test(*_, returnValue):  # noqa: N803
        assert returnValue == 4
        return "42"

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test(returnValue: 4) }")
    assert result.errors is None
    assert result.data == {"test": 42}


def test_custom_resolver_is_called_with_input_type_value_as_dict():
    type_defs = """
        type Query {
            test(data: TestInput): Int
        }

        input TestInput {
            value: Int
        }
    """

    query = QueryType()

    @query.field("test")
    def resolve_test(*_, data):
        assert data == {"value": 4}
        return "42"

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test(data: { value: 4 }) }")
    assert result.errors is None
    assert result.data == {"test": 42}
