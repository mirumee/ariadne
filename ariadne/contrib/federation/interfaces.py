from typing import Optional, cast

from graphql import GraphQLNamedType
from graphql.type import GraphQLSchema

from ...interfaces import InterfaceType
from ...types import Resolver
from ...utils import type_get_extension, type_implements_interface, type_set_extension


class FederatedInterfaceType(InterfaceType):
    """Add `__referenceResolver` to interfaces as per apollo-federation."""

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

            for object_type in schema.type_map.values():
                if type_implements_interface(
                    self.name, object_type
                ) and not type_get_extension(object_type, "__resolve_reference__"):
                    type_set_extension(
                        object_type,
                        "__resolve_reference__",
                        self._reference_resolver,
                    )
