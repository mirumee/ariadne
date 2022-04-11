from typing import Callable, Dict

from graphql.type import GraphQLSchema

from .objects import ObjectType
from .types import Subscriber


class SubscriptionType(ObjectType):
    _subscribers: Dict[str, Subscriber]

    def __init__(self) -> None:
        super().__init__("Subscription")
        self._subscribers = {}

    def source(self, name: str) -> Callable[[Subscriber], Subscriber]:
        if not isinstance(name, str):
            raise ValueError(
                'source decorator should be passed a field name: @foo.source("name")'
            )
        return self.create_register_subscriber(name)

    def create_register_subscriber(
        self, name: str
    ) -> Callable[[Subscriber], Subscriber]:
        def register_subscriber(generator: Subscriber) -> Subscriber:
            self._subscribers[name] = generator
            return generator

        return register_subscriber

    def set_source(self, name, generator: Subscriber) -> Subscriber:
        self._subscribers[name] = generator
        return generator

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        self.bind_resolvers_to_graphql_type(graphql_type)
        self.bind_subscribers_to_graphql_type(graphql_type)

    def bind_subscribers_to_graphql_type(self, graphql_type):
        for field, subscriber in self._subscribers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )

            graphql_type.fields[field].subscribe = subscriber
