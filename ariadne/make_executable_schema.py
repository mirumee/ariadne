from graphql import GraphQLSchema, parse
from graphql.utils.build_ast_schema import build_ast_schema

from .add_resolve_functions_to_schema import add_resolve_functions_to_schema


def build_schema(type_defs: str) -> GraphQLSchema:
    ast_schema = parse(type_defs)
    return build_ast_schema(ast_schema)


def make_executable_schema(type_defs: str, resolvers: dict) -> GraphQLSchema:
    schema = build_schema(type_defs)
    add_resolve_functions_to_schema(schema, resolvers)
    return schema
