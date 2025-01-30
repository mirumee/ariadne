from base64 import b64decode
from inspect import iscoroutinefunction
from typing import Optional, Tuple

from graphql.pyutils import is_awaitable
from graphql.type import GraphQLSchema

from ariadne import InterfaceType, ObjectType
from ariadne.contrib.relay.arguments import (
    ConnectionArguments,
    ConnectionArgumentsTypeUnion,
)
from ariadne.contrib.relay.types import (
    ConnectionResolver,
    GlobalIDDecoder,
    GlobalIDTuple,
)
from ariadne.types import Resolver


def decode_global_id(kwargs) -> GlobalIDTuple:
    return GlobalIDTuple(*b64decode(kwargs["id"]).decode().split(":"))


class RelayObjectType(ObjectType):
    _node_resolver: Optional[Resolver] = None

    def __init__(
        self,
        name: str,
        connection_arguments_class: ConnectionArgumentsTypeUnion = ConnectionArguments,
    ) -> None:
        super().__init__(name)
        self.connection_arguments_class = connection_arguments_class

    def resolve_wrapper(self, resolver: ConnectionResolver):
        def wrapper(obj, info, *args, **kwargs):
            connection_arguments = self.connection_arguments_class(**kwargs)
            if iscoroutinefunction(resolver):

                async def async_my_extension():
                    relay_connection = await resolver(
                        obj, info, connection_arguments, *args, **kwargs
                    )
                    if is_awaitable(relay_connection):
                        relay_connection = await relay_connection
                    return {
                        "edges": relay_connection.get_edges(),
                        "pageInfo": relay_connection.get_page_info(
                            connection_arguments
                        ),
                    }

                return async_my_extension()

            relay_connection = resolver(
                obj, info, connection_arguments, *args, **kwargs
            )
            return {
                "edges": relay_connection.get_edges(),
                "pageInfo": relay_connection.get_page_info(connection_arguments),
            }

        return wrapper

    def connection(self, name: str):
        def decorator(resolver: ConnectionResolver) -> ConnectionResolver:
            self.set_field(name, self.resolve_wrapper(resolver))
            return resolver

        return decorator

    def node_resolver(self, resolver: Resolver):
        self._node_resolver = resolver
        return resolver

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        super().bind_to_schema(schema)

        if callable(self._node_resolver):
            graphql_type = schema.type_map.get(self.name)
            setattr(
                graphql_type,
                "__resolve_node__",
                self._node_resolver,
            )


class RelayNodeInterfaceType(InterfaceType):
    def __init__(
        self,
        type_resolver: Optional[Resolver] = None,
    ) -> None:
        super().__init__("Node", type_resolver)


class RelayQueryType(RelayObjectType):
    def __init__(
        self,
        node: Optional[RelayNodeInterfaceType] = None,
        global_id_decoder: GlobalIDDecoder = decode_global_id,
    ) -> None:
        super().__init__("Query")
        if node is None:
            node = RelayNodeInterfaceType()
        self.node = node
        self.set_field("node", self.resolve_node)
        self.global_id_decoder = global_id_decoder

    @property
    def bindables(self) -> Tuple["RelayQueryType", "RelayNodeInterfaceType"]:
        return (self, self.node)

    def get_node_resolver(self, type_name, schema: GraphQLSchema) -> Resolver:
        type_object = schema.get_type(type_name)
        try:
            return getattr(type_object, "__resolve_node__")
        except AttributeError as exc:
            raise ValueError(f"No node resolver for type {type_name}") from exc

    def resolve_node(self, obj, info, *args, **kwargs):
        type_name, _ = self.global_id_decoder(kwargs)

        resolver = self.get_node_resolver(type_name, info.schema)

        if iscoroutinefunction(resolver):

            async def async_my_extension():
                result = await resolver(obj, info, *args, **kwargs)
                if is_awaitable(result):
                    result = await result
                return result

            return async_my_extension()
        return resolver(obj, info, *args, **kwargs)
