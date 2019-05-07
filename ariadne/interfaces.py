from typing import Optional, cast

from graphql.type import (
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLSchema,
)

from .objects import ObjectType
from .types import Resolver


class InterfaceType(ObjectType):
    _resolve_type: Optional[Resolver]

    def __init__(self, name: str, type_resolver: Optional[Resolver] = None) -> None:
        super().__init__(name)
        self._resolve_type = type_resolver

    def set_type_resolver(self, type_resolver: Resolver) -> Resolver:
        self._resolve_type = type_resolver
        return type_resolver

    # Alias type resolver for consistent decorator API
    type_resolver = set_type_resolver

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLInterfaceType, graphql_type)

        graphql_type.resolve_type = self._resolve_type
        self.bind_resolvers_to_graphql_type(graphql_type)

        for object_type in schema.type_map.values():
            if _type_implements_interface(self.name, object_type):
                self.bind_resolvers_to_graphql_type(object_type, replace_existing=False)

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        if not graphql_type:
            raise ValueError("Interface %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLInterfaceType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (
                    self.name,
                    type(graphql_type).__name__,
                    GraphQLInterfaceType.__name__,
                )
            )


def _type_implements_interface(interface: str, graphql_type: GraphQLNamedType) -> bool:
    if not isinstance(graphql_type, GraphQLObjectType):
        return False
    return interface in [i.name for i in graphql_type.interfaces]
