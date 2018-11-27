import pytest
from graphql import GraphQLSchema

from ariadne import Schema
from ariadne.schema_types import ObjectType, ScalarType

type_defs = """
    type Query {
        hello: String
    }

    scalar Datetime
"""


def test_class_takes_sdl_string_and_builds_schema():
    schema = Schema(type_defs)
    assert isinstance(schema._schema, GraphQLSchema)


def test_class_takes_list_of_sdl_strings_and_builds_schema():
    extra_typedef = """
        type Log {
            text: String!
        }
    """

    schema = Schema([type_defs, extra_typedef])
    assert isinstance(schema._schema, GraphQLSchema)


def test_type_getter_returns_type_proxy_for_existing_type():
    schema = Schema(type_defs)
    assert isinstance(schema.type("Query"), ObjectType)


def test_type_getter_returns_scalar_proxy_for_existing_scalar():
    schema = Schema(type_defs)
    assert isinstance(schema.type("Datetime"), ScalarType)


def test_type_getter_raises_value_error_for_undefined_type():
    schema = Schema(type_defs)
    with pytest.raises(ValueError):
        schema.type("Undefined")
