from base64 import b64decode
from inspect import iscoroutinefunction
from typing import Dict, Optional, Tuple

from graphql.pyutils import is_awaitable

from ariadne import InterfaceType, ObjectType, QueryType
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


class RelayNodeInterfaceType(InterfaceType):
    def __init__(
        self,
        type_resolver: Optional[Resolver] = None,
        global_id_decoder: Optional[GlobalIDDecoder] = decode_global_id,
    ) -> None:
        super().__init__("Node", type_resolver)
        self._object_resolvers: Dict[str, Resolver] = {}
        self.global_id_decoder = global_id_decoder

    def node_resolver(self, name: str):
        def decorator(resolver):
            self.set_node_resolver(name, resolver)
            return resolver

        return decorator

    def set_node_resolver(self, name: str, resolver):
        self._object_resolvers[name] = resolver

    def get_node_resolver(self, type_name: str):
        try:
            return self._object_resolvers[type_name]
        except KeyError as exc:
            raise ValueError(f"No object resolver for type {type_name}") from exc


class RelayQueryType(QueryType):
    def __init__(
        self,
        *args,
        node=None,
        node_field_resolver=None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        if not node:
            node = RelayNodeInterfaceType()
        self.node = node
        if not node_field_resolver:
            node_field_resolver = self.default_resolve_node
        self.set_field("node", node_field_resolver)

    @property
    def bindables(self) -> Tuple["RelayQueryType", "RelayNodeInterfaceType"]:
        return (self, self.node)

    def default_resolve_node(self, obj, info, *args, **kwargs):
        type_name, _ = self.node.global_id_decoder(kwargs)
        resolver = self.node.get_node_resolver(type_name)
        if iscoroutinefunction(resolver):

            async def async_my_extension():
                result = await resolver(obj, info, *args, **kwargs)
                if is_awaitable(result):
                    result = await result
                return result

            return async_my_extension()
        return resolver(obj, info, *args, **kwargs)


class RelayObjectType(ObjectType):
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
