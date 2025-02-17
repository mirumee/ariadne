from typing import Optional, cast

from graphql import GraphQLNamedType
from graphql.type import GraphQLSchema

from ...objects import ObjectType
from ...types import Resolver
from ...utils import type_set_extension


class FederatedObjectType(ObjectType):
    """Add `__referenceResolver` to objects as per apollo-federation."""

    _reference_resolver: Optional[Resolver] = None

    def reference_resolver(self, arg: Optional[Resolver] = None) -> Resolver:
        def register_reference_resolver(f: Resolver) -> Resolver:
            self._reference_resolver = f
            return f

        if callable(arg):
            return register_reference_resolver(arg)
        return register_reference_resolver

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        super().bind_to_schema(schema)

        if callable(self._reference_resolver):
            graphql_type = schema.type_map.get(self.name)
            graphql_type = cast(GraphQLNamedType, graphql_type)
            type_set_extension(
                graphql_type,
                "__resolve_reference__",
                self._reference_resolver,
            )
