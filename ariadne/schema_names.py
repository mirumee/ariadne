from typing import Callable, Optional, Tuple

from graphql import (
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLSchema,
)

from .resolvers import resolve_to
from .utils import convert_camel_case_to_snake

"""
A type of a function implementing a strategy for names conversion in schema. 
Passed as an option to `make_executable_schema` and `convert_schema_names` 
functions.

Takes three arguments:

`name`: a `str` with schema name to convert.

`schema`: the GraphQL schema in which names are converted.

`path`: a tuple of `str` representing a path to the schema item which name 
is being converted.

Returns a string with the Python name to use.
"""
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
    """Set mappings in GraphQL schema from `camelCase` names to `snake_case`.

    This function scans GraphQL schema and:

    If objects field has name in `camelCase` and this field doesn't have a
    resolver already set on it, new resolver is assigned to it that resolves
    it's value from object attribute or dict key named like `snake_case`
    version of field's name.

    If object's field has argument in `camelCase` and this argument doesn't have
    the `out_name` attribute already set, this attribute is populated with
    argument's name converted to `snake_case`

    If input's field has name in `camelCase` and it's `out_name` attribute is
    not already set, this attribute is populated with field's name converted
    to `snake_case`.

    Schema is mutated in place.

    Generally you shouldn't call this function yourself, as its part of
    `make_executable_schema` logic, but its part of public API for other
    libraries to use.

    # Required arguments

    `schema`: a GraphQL schema to update.

    `name_converter`: an `SchemaNameConverter` function to use to convert the
    names from `camelCase` to `snake_case`. If not provided, default one
    based on `convert_camel_case_to_snake` is used.
    """
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
