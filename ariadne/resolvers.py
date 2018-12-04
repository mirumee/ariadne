from typing import Any, Callable, Dict, overload

from graphql.type import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLSchema,
)

from .types import Bindable, Resolver
from .utils import convert_camel_case_to_snake


class ResolverMap(Bindable):
    _resolvers: Dict[str, Resolver]

    def __init__(self, name: str) -> None:
        self.name = name
        self._resolvers = {}

    @overload
    def field(self, name: str) -> Callable[[Resolver], Resolver]:
        pass  # pragma: no cover

    @overload
    def field(  # pylint: disable=function-redefined
        self, name: str, *, resolver: Resolver
    ) -> Resolver:  # pylint: disable=function-redefined
        pass  # pragma: no cover

    def field(self, name, *, resolver=None):  # pylint: disable=function-redefined
        if not resolver:
            return self.create_register_resolver(name)
        self._resolvers[name] = resolver
        return resolver

    def create_register_resolver(self, name: str) -> Callable[[Resolver], Resolver]:
        def register_resolver(f: Resolver) -> Resolver:
            self._resolvers[name] = f
            return f

        return register_resolver

    def alias(self, name: str, to: str) -> None:
        self._resolvers[name] = resolve_to(to)

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)

        for field, resolver in self._resolvers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )

            graphql_type.fields[field].resolve = resolver

    def validate_graphql_type(self, graphql_type: str) -> None:
        if not graphql_type:
            raise ValueError("Type %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLObjectType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLObjectType.__name__)
            )


class FallbackResolversSetter(Bindable):
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
