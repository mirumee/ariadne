from typing import Any

from graphql.type import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLSchema,
)

from .types import Resolver, SchemaBindable
from .utils import convert_camel_case_to_snake


class FallbackResolversSetter(SchemaBindable):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        for type_object in schema.type_map.values():
            if isinstance(type_object, GraphQLObjectType):
                self.add_resolvers_to_object_fields(type_object)

    def add_resolvers_to_object_fields(self, type_object) -> None:
        for field_name, field_object in type_object.fields.items():
            self.add_resolver_to_field(field_name, field_object)

    def add_resolver_to_field(self, _: str, field_object: GraphQLField) -> None:
        if field_object.resolve is None:
            field_object.resolve = default_resolver


class SnakeCaseFallbackResolversSetter(FallbackResolversSetter):
    def add_resolver_to_field(
        self, field_name: str, field_object: GraphQLField
    ) -> None:
        if field_object.resolve is None:
            field_name = convert_camel_case_to_snake(field_name)
            field_object.resolve = resolve_to(field_name)


fallback_resolvers = FallbackResolversSetter()
snake_case_fallback_resolvers = SnakeCaseFallbackResolversSetter()


def resolve_parent_field(parent: Any, name: str) -> Any:
    if isinstance(parent, dict):
        return parent.get(name)
    return getattr(parent, name, None)


def default_resolver(parent: Any, info: GraphQLResolveInfo) -> Resolver:
    return resolve_parent_field(parent, info.field_name)


def resolve_to(name: str) -> Resolver:
    def resolver(parent: Any, *_) -> Any:
        return resolve_parent_field(parent, name)

    return resolver
