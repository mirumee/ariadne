from typing import Iterator, List, Union

from graphql import GraphQLObjectType, GraphQLSchema, build_schema

from .resolvers import resolve_to
from .utils import convert_camel_case_to_snake


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: Union[dict, List[dict]] = []
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    schema = build_schema(type_defs)

    if isinstance(resolvers, list):
        for type_resolvers in resolvers:
            type_resolvers.bind_to_schema(schema)
    else:
        resolvers.bind_to_schema(schema)

    set_case_converting_resolvers(schema)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def set_case_converting_resolvers(schema: GraphQLSchema):
    for type_object in schema.type_map.values():
        if isinstance(type_object, GraphQLObjectType):
            add_resolve_functions_to_object(type_object)


def add_resolve_functions_to_object(obj: GraphQLObjectType):
    for field_name, field_object in obj.fields.items():
        if field_object.resolve is None:
            python_name = convert_camel_case_to_snake(field_name)
            field_object.resolve = resolve_to(python_name)
