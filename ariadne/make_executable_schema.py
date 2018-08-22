from typing import List, Union

from graphql import GraphQLSchema

from .add_resolve_functions_to_schema import add_resolve_functions_to_schema
from .build_schema_from_type_definitions import build_schema_from_type_definitions


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: dict
) -> GraphQLSchema:
    schema = build_schema_from_type_definitions(type_defs)
    add_resolve_functions_to_schema(schema, resolvers)
    return schema
