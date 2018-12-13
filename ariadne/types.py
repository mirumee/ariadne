from typing import Any, Callable
from typing_extensions import Protocol

from graphql.type import GraphQLSchema


class Bindable(Protocol):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass  # pragma: no cover


# Note: this should be [Any, GraphQLResolveInfo, **kwargs],
# but this is not achieveable with python types yet:
# https://github.com/mirumee/ariadne/pull/79
Resolver = Callable[..., Any]

ScalarOperation = Callable[[Any], Any]
