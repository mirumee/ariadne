from collections import defaultdict
from itertools import chain
from typing import Iterator, List, Union

from graphql import GraphQLObjectType, GraphQLScalarType, GraphQLSchema, build_schema


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: Union[dict, List[dict]]
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    schema = build_schema(type_defs)

    if isinstance(resolvers, list):
        for resolvers_dict in resolvers:
            add_resolve_functions_to_schema(schema, resolvers_dict)
    else:
        add_resolve_functions_to_schema(schema, resolvers)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def add_resolve_functions_to_schema(schema: GraphQLSchema, resolvers: dict):
    for type_name, type_object in schema.type_map.items():
        if isinstance(type_object, GraphQLObjectType):
            add_resolve_functions_to_object(type_name, type_object, resolvers)
        if isinstance(type_object, GraphQLScalarType):
            add_resolve_functions_to_scalar(type_name, type_object, resolvers)


def add_resolve_functions_to_object(name: str, obj: GraphQLObjectType, resolvers: dict):
    type_resolvers = resolvers.get(name, {})
    for field_name, field_object in obj.fields.items():
        field_resolver = type_resolvers.get(field_name)
        if field_resolver:
            field_object.resolve = field_resolver


def add_resolve_functions_to_scalar(name: str, obj: GraphQLObjectType, resolvers: dict):
    scalar_resolvers = resolvers.get(name, {})

    serialize = scalar_resolvers.get("serialize", obj.serialize)
    obj.serialize = serialize

    parse_literal = scalar_resolvers.get("parse_literal", obj.parse_literal)
    obj.parse_literal = parse_literal

    parse_value = scalar_resolvers.get("parse_value", obj.parse_value)
    obj.parse_value = parse_value