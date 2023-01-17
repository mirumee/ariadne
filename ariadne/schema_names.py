from typing import Callable, Optional, Type, Union

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLSchema,
)

from .resolvers import resolve_to
from .utils import convert_camel_case_to_snake

SchemaNameConverter = Callable[
    [str, Type[Union[GraphQLArgument, GraphQLField, GraphQLInputField]]], str
]

GRAPHQL_SPEC_TYPES = (
    "__Directive",
    "__EnumValue",
    "__Field",
    "__InputValue",
    "__Schema",
    "__Type",
)


def convert_schema_names(
    schema: GraphQLSchema,
    name_converter: Optional[SchemaNameConverter],
) -> None:
    name_converter = name_converter or default_schema_name_converter

    for type_name, graphql_type in schema.type_map.items():
        if (
            isinstance(graphql_type, GraphQLObjectType)
            and type_name not in GRAPHQL_SPEC_TYPES
        ):
            convert_names_in_schema_object(graphql_type, name_converter)
        if isinstance(graphql_type, GraphQLInputObjectType):
            convert_names_in_schema_input(graphql_type, name_converter)


def convert_names_in_schema_object(
    graphql_type: GraphQLObjectType,
    name_converter: SchemaNameConverter,
) -> None:
    for field_name, field in graphql_type.fields.items():
        if field.args:
            convert_names_in_schema_args(field, name_converter)

        if field.resolve or field_name.lower() == field_name:
            continue

        field.resolve = resolve_to(name_converter(field_name, GraphQLField))


def convert_names_in_schema_args(
    graphql_type: GraphQLField,
    name_converter: SchemaNameConverter,
) -> None:
    for arg_name, arg in graphql_type.args.items():
        if arg.out_name or arg_name.lower() == arg_name:
            continue

        arg.out_name = name_converter(arg_name, GraphQLInputField)


def convert_names_in_schema_input(
    graphql_type: GraphQLInputObjectType,
    name_converter: SchemaNameConverter,
) -> None:
    for field_name, field in graphql_type.fields.items():
        if field.out_name or field_name.lower() == field_name:
            continue

        field.out_name = name_converter(field_name, GraphQLInputField)


def default_schema_name_converter(graphql_name: str, _graphql_type) -> str:
    return convert_camel_case_to_snake(graphql_name)
