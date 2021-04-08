from typing import Any

from graphql import default_field_resolver
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
            field_object.resolve = default_field_resolver


class SnakeCaseFallbackResolversSetter(FallbackResolversSetter):
    def add_resolver_to_field(
        self, field_name: str, field_object: GraphQLField
    ) -> None:
        if field_object.resolve is None:
            field_name = convert_camel_case_to_snake(field_name)
            field_object.resolve = resolve_to(field_name)


fallback_resolvers = FallbackResolversSetter()
snake_case_fallback_resolvers = SnakeCaseFallbackResolversSetter()


def resolve_parent_field(parent: Any, field_name: str) -> Any:
    if isinstance(parent, dict):
        return parent.get(field_name)
    return getattr(parent, field_name, None)


def resolve_to(field_name: str) -> Resolver:
    def resolver(parent: Any, info: GraphQLResolveInfo, **kwargs) -> Any:
        value = resolve_parent_field(parent, field_name)
        if callable(value):
            return value(info, **kwargs)
        return value

    # pylint: disable=protected-access
    resolver._ariadne_alias_resolver = True  # type: ignore
    return resolver


def is_default_resolver(resolver: Resolver) -> bool:
    # pylint: disable=comparison-with-callable
    if resolver == default_field_resolver:
        return True
    return hasattr(resolver, "_ariadne_alias_resolver")
