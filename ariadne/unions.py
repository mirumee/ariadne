from typing import Optional, cast

from graphql.type import GraphQLNamedType, GraphQLUnionType, GraphQLSchema

from .types import Resolver, SchemaBindable


class UnionType(SchemaBindable):
    _resolve_type: Optional[Resolver]

    def __init__(self, name: str, type_resolver: Optional[Resolver] = None) -> None:
        self.name = name
        self._resolve_type = type_resolver

    def set_type_resolver(self, type_resolver: Resolver) -> Resolver:
        self._resolve_type = type_resolver
        return type_resolver

    # Alias type resolver for consistent decorator API
    type_resolver = set_type_resolver

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLUnionType, graphql_type)
        graphql_type.resolve_type = self._resolve_type

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        if not graphql_type:
            raise ValueError("Type %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLUnionType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLUnionType.__name__)
            )
