from typing import Callable, Optional, Tuple

from graphql import (
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLSchema,
)

from .resolvers import resolve_to
from .utils import convert_camel_case_to_snake

SchemaNameConverter = Callable[[str, GraphQLSchema, Tuple[str, ...]], str]

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
            convert_names_in_schema_object(name_converter, graphql_type, schema)
        if isinstance(graphql_type, GraphQLInputObjectType):
            convert_names_in_schema_input(name_converter, graphql_type, schema)


def convert_names_in_schema_object(
    name_converter: SchemaNameConverter,
    graphql_object: GraphQLObjectType,
    schema: GraphQLSchema,
) -> None:
    for field_name, field in graphql_object.fields.items():
        if field.args:
            convert_names_in_schema_args(
                name_converter, field, schema, graphql_object.name, field_name
            )

        if field.resolve or field_name.lower() == field_name:
            continue

        field.resolve = resolve_to(
            name_converter(field_name, schema, (graphql_object.name, field_name))
        )


def convert_names_in_schema_args(
    name_converter: SchemaNameConverter,
    graphql_field: GraphQLField,
    schema: GraphQLSchema,
    object_name: str,
    field_name: str,
) -> None:
    for arg_name, arg in graphql_field.args.items():
        if arg.out_name or arg_name.lower() == arg_name:
            continue

        arg.out_name = name_converter(
            arg_name, schema, (object_name, field_name, arg_name)
        )


def convert_names_in_schema_input(
    name_converter: SchemaNameConverter,
    graphql_input: GraphQLInputObjectType,
    schema: GraphQLSchema,
) -> None:
    for field_name, field in graphql_input.fields.items():
        if field.out_name or field_name.lower() == field_name:
            continue

        field.out_name = name_converter(
            field_name, schema, (graphql_input.name, field_name)
        )


def default_schema_name_converter(graphql_name: str, *_) -> str:
    return convert_camel_case_to_snake(graphql_name)
