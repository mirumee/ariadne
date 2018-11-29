from typing import Any, Callable, Dict

from graphql.type import GraphQLObjectType, GraphQLResolveInfo, GraphQLSchema

from .types import Bindable, Resolver
from .utils import convert_camel_case_to_snake


class ResolverMap(Bindable):
    _resolvers: Dict[str, Resolver]

    def __init__(self, name: str) -> None:
        self.name = name
        self._resolvers = {}

    def field(self, name: str) -> Callable[[Resolver], Resolver]:
        def register_resolver(f):
            self._resolvers[name] = f
            return f

        return register_resolver

    def alias(self, name: str, to: str):
        self._resolvers[name] = resolve_to(to)

    def bind_to_schema(self, schema: GraphQLSchema):
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)

        for field, resolver in self._resolvers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )

            graphql_type.fields[field].resolve = resolver

    def validate_graphql_type(self, graphql_type: str):
        if not graphql_type:
            raise ValueError("Type %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLObjectType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLObjectType.__name__)
            )


def resolve_parent_field(parent: Any, name: str, **kwargs: dict) -> Any:
    if isinstance(parent, dict):
        value = parent.get(name)
    else:
        value = getattr(parent, name, None)
    if callable(value):
        return value(**kwargs)
    return value


def default_resolver(parent, info: GraphQLResolveInfo, **kwargs) -> Resolver:
    return resolve_parent_field(parent, info.field_name, **kwargs)


def resolve_to(name: str) -> Resolver:
    def resolver(parent, *_, **kwargs):
        return resolve_parent_field(parent, name, **kwargs)

    return resolver


def set_default_resolvers(schema: GraphQLSchema):
    for type_object in schema.type_map.values():
        if isinstance(type_object, GraphQLObjectType):
            set_default_resolve_functions_on_object(type_object)


def set_default_resolve_functions_on_object(obj: GraphQLObjectType):
    for field_name, field_object in obj.fields.items():
        if field_object.resolve is None:
            field_name = convert_camel_case_to_snake(field_name)
            field_object.resolve = resolve_to(field_name)
