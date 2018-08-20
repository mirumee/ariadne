from typing import List, Union

from graphql import GraphQLSchema
from graphql.language.ast import Document

from .add_resolve_functions_to_schema import add_resolve_functions_to_schema
from .build_schema_from_type_definitions import build_schema_from_type_definitions

TypeDef = Union[str, Document]
TypeDefs = Union[TypeDef, List[TypeDef]]


def make_executable_schema(type_defs: TypeDefs, resolvers: dict) -> GraphQLSchema:
    schema = build_schema_from_type_definitions(type_defs)
    add_resolve_functions_to_schema(schema, resolvers)
    return schema
