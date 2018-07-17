from graphql import GraphQLObjectType, GraphQLScalarType, GraphQLSchema, parse
from graphql.utils.build_ast_schema import build_ast_schema

from .default_resolver import default_resolver


def build_schema(schema_description: str) -> GraphQLSchema:
    ast_schema = parse(schema_description)
    return build_ast_schema(ast_schema)


def make_executable_schema(schema: GraphQLSchema, resolvers: dict) -> GraphQLSchema:
    for type_name, type_object in schema.get_type_map().items():
        if isinstance(type_object, GraphQLScalarType):
            serializer = resolvers.get(type_name, type_object.serialize)
            print(type_name, serializer)
            type_object.serialize = serializer
        if isinstance(type_object, GraphQLObjectType):
            type_resolver = resolvers.get(type_name, {})
            for field_name, field_object in type_object.fields.items():
                field_resolver = type_resolver.get(field_name) or default_resolver
                field_object.resolver = field_resolver
