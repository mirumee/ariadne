from typing import Callable, Dict, Optional, cast

from graphql.type import GraphQLNamedType, GraphQLObjectType, GraphQLSchema

from .resolvers import resolve_to
from .types import Resolver, SchemaBindable


class ObjectType(SchemaBindable):
    _resolvers: Dict[str, Resolver]

    def __init__(self, name: str) -> None:
        self.name = name
        self._resolvers = {}

    def field(self, name: str) -> Callable[[Resolver], Resolver]:
        if not isinstance(name, str):
            raise ValueError(
                'field decorator should be passed a field name: @foo.field("name")'
            )
        return self.create_register_resolver(name)

    def create_register_resolver(self, name: str) -> Callable[[Resolver], Resolver]:
        def register_resolver(f: Resolver) -> Resolver:
            self._resolvers[name] = f
            return f

        return register_resolver

    def set_field(self, name, resolver: Resolver) -> Resolver:
        self._resolvers[name] = resolver
        return resolver

    def set_alias(self, name: str, to: str) -> None:
        self._resolvers[name] = resolve_to(to)

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLObjectType, graphql_type)
        self.bind_resolvers_to_graphql_type(graphql_type)

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
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


class QueryType(ObjectType):
    """Convenience class for defining Query type"""

    def __init__(self) -> None:
        super().__init__("Query")


class MutationType(ObjectType):
    """Convenience class for defining Mutation type"""

    def __init__(self) -> None:
        super().__init__("Mutation")
