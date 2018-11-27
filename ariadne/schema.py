from typing import List, Union

from graphql import GraphQLObjectType, GraphQLScalarType, GraphQLSchema, build_schema

from .resolvers import resolve_to
from .schema_types import ObjectType, ScalarType
from .utils import convert_camel_case_to_snake, join_type_defs


class Schema:
    _schema: GraphQLSchema

    def __init__(self, type_defs: Union[str, List[str]]):
        if isinstance(type_defs, list):
            type_defs = join_type_defs(type_defs)
        self._schema = build_schema(type_defs)

    def type(self, type_name: str) -> Union[ObjectType, ScalarType]:
        graphql_type = self._schema.type_map.get(type_name)
        if not graphql_type:
            valid_types = filter(
                lambda t: not t.startswith("__"), self._schema.type_map.keys()
            )
            raise ValueError(
                "%s type is not defined in this schema. Defined types: %s"
                % (type_name, ", ".join(valid_types))
            )

        if isinstance(graphql_type, GraphQLObjectType):
            return ObjectType(graphql_type)
        if isinstance(graphql_type, GraphQLScalarType):
            return ScalarType(graphql_type)

    def make_executable(self) -> GraphQLSchema:
        add_default_resolvers_to_schema(self._schema)
        return self._schema


def add_default_resolvers_to_schema(schema: GraphQLSchema):
    for type_object in schema.type_map.values():
        if isinstance(type_object, GraphQLObjectType):
            add_resolve_functions_to_object(type_object)


def add_resolve_functions_to_object(obj: GraphQLObjectType):
    for field_name, field_object in obj.fields.items():
        if field_object.resolve is None:
            python_name = convert_camel_case_to_snake(field_name)
            field_object.resolve = resolve_to(python_name)