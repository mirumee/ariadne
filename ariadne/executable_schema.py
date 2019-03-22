from typing import List, Union

from graphql import GraphQLSchema, build_schema

from .types import SchemaBindable


def make_executable_schema(
    type_defs: Union[str, List[str]],
    resolvers: Union[SchemaBindable, List[SchemaBindable], None] = None,
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    schema = build_schema(type_defs)

    if isinstance(resolvers, list):
        for obj in resolvers:
            obj.bind_to_schema(schema)
    elif resolvers:
        resolvers.bind_to_schema(schema)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)
