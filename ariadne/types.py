from typing import Any, Callable
from typing_extensions import Protocol

from graphql.type import GraphQLResolveInfo, GraphQLSchema


class Bindable(Protocol):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass


Resolver = Callable[[Any, GraphQLResolveInfo], Any]

ScalarOperation = Callable[[Any], Any]
