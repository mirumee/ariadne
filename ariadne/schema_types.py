from graphql import GraphQLField, GraphQLObjectType, GraphQLScalarType
from typing import Any, Callable

from .resolvers import resolve_to


class ScalarType:
    def __init__(self, scalar: GraphQLScalarType):
        self.scalar = scalar

    def serialize(self):
        def register_serialize(serialize: Callable) -> Any:
            self.scalar.serialize = serialize
            return serialize

        return register_serialize

    def parse_value(self):
        def register_parse_value(parse_value: Callable) -> Any:
            self.scalar.parse_value = parse_value
            return parse_value

        return register_parse_value

    def parse_literal(self):
        def register_parse_value(parse_literal: Callable) -> Any:
            self.scalar.parse_literal = parse_literal
            return parse_literal

        return register_parse_literal


class ObjectType:
    def __init__(self, object: GraphQLObjectType):
        self.object = object

    def field(self, field_name: str) -> GraphQLField:
        field = self.object.fields.get(field_name)
        if not field:
            valid_fields = self.object.fields.keys()
            raise ValueError(
                "%s field is not defined in this object. Defined fields: %s"
                % (field_name, ", ".join(valid_fields))
            )
        return field

    def alias(self, field_name: str, to: str):
        field = self.field(field_name)
        field.resolve = resolve_to(to)

    def resolve(self, field_name: str):
        def register_resolver(resolver: Callable) -> Any:
            field = self.field(field_name)
            field.resolve = resolver
            return resolver

        return register_resolver
