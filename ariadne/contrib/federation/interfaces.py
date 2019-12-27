from graphql.type import GraphQLSchema

from ...interfaces import InterfaceType
from ...types import Resolver


class FederatedInterfaceType(InterfaceType):
    """Add `__referenceResolver` to interfaces as per apollo-federation."""

    _reference_resolver: Resolver = None

    def reference_resolver(self, arg: Resolver = None) -> Resolver:
        def register_reference_resolver(f: Resolver) -> Resolver:
            self._reference_resolver = f
            return f

        if callable(arg):
            return register_reference_resolver(arg)
        else:
            return register_reference_resolver

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        super().bind_to_schema(schema)

        if callable(self._reference_resolver):
            graphql_type = schema.type_map.get(self.name)
            setattr(
                graphql_type,
                '__resolve_reference__',
                self._reference_resolver,
            )
