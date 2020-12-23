from typing import Optional

from graphql.type import GraphQLSchema

from ...objects import ObjectType
from ...types import Resolver


class FederatedObjectType(ObjectType):
    """Add `__referenceResolver` to objects as per apollo-federation."""

    _reference_resolver: Optional[Resolver] = None

    def reference_resolver(self, arg: Resolver = None) -> Resolver:
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
            setattr(
                graphql_type,
                "__resolve_reference__",
                self._reference_resolver,
            )
