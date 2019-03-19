from typing import Any, Callable, Dict, overload

from graphql.type import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLSchema,
)

from .types import Bindable, Resolver, Subscriber
from .utils import convert_camel_case_to_snake


class ObjectType(Bindable):
    _resolvers: Dict[str, Resolver]
    _subscribers: Dict[str, Subscriber]

    def __init__(self, name: str) -> None:
        self.name = name
        self._resolvers = {}
        self._subscribers = {}

    def field(self, name: str) -> Callable[[Resolver], Resolver]:
        return self.create_register_resolver(name)

    def create_register_resolver(self, name: str) -> Callable[[Resolver], Resolver]:
        def register_resolver(f: Resolver) -> Resolver:
            self._resolvers[name] = f
            return f

        return register_resolver

    def set_field(
        self, name, resolver=None
    ) -> Resolver:  # pylint: disable=function-redefined
        if not resolver:
            return self.create_register_resolver(name)
        self._resolvers[name] = resolver
        return resolver

    @overload
    def source(self, name: str) -> Callable[[Subscriber], Subscriber]:
        pass  # pragma: no cover

    @overload
    def source(  # pylint: disable=function-redefined
        self, name: str, *, generator: Subscriber
    ) -> Subscriber:  # pylint: disable=function-redefined
        pass  # pragma: no cover

    def source(self, name, *, generator=None):  # pylint: disable=function-redefined
        if not generator:
            return self.create_register_subscriber(name)
        self._subscribers[name] = generator
        return generator

    def create_register_subscriber(
        self, name: str
    ) -> Callable[[Subscriber], Subscriber]:
        def register_subscriber(generator: Subscriber) -> Subscriber:
            self._subscribers[name] = generator
            return generator

        return register_subscriber

    def set_alias(self, name: str, to: str) -> None:
        self._resolvers[name] = resolve_to(to)

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        self.bind_resolvers_to_graphql_type(graphql_type)
        self.bind_subscribers_to_graphql_type(graphql_type)

    def validate_graphql_type(self, graphql_type: str) -> None:
        if not graphql_type:
            raise ValueError("Type %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLObjectType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLObjectType.__name__)
            )

    def bind_resolvers_to_graphql_type(self, graphql_type, replace_existing=True):
        for field, resolver in self._resolvers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )
            if graphql_type.fields[field].resolve is None or replace_existing:
                graphql_type.fields[field].resolve = resolver

    def bind_subscribers_to_graphql_type(self, graphql_type):
        for field, subscriber in self._subscribers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )

            graphql_type.fields[field].subscribe = subscriber


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
