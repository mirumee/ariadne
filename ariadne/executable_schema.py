from typing import List, Union

from graphql import GraphQLSchema

from .build_schema import build_schema_from_type_definitions
from .resolvers import add_resolve_functions_to_schema


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: dict
) -> GraphQLSchema:
    schema = build_schema_from_type_definitions(type_defs)
    add_resolve_functions_to_schema(schema, resolvers)
    return schema
