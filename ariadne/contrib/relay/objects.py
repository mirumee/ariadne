from inspect import iscoroutinefunction

from graphql.pyutils import is_awaitable

from ariadne import InterfaceType, ObjectType, QueryType
from ariadne.contrib.relay.arguments import (
    ConnectionArguments,
    ConnectionArgumentsTypeUnion,
)
from ariadne.contrib.relay.types import ConnectionResolver


class RelayQueryType(QueryType):
    def __init__(
        self, *args, node_type_resolver=None, node_field_resolver=None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.node = InterfaceType("Node", node_type_resolver)
        self.set_field("node", node_field_resolver)

    @property
    def bindables(self):
        return [self, self.node]


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
