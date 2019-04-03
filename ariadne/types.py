from typing import Any, AsyncGenerator, Callable, List
from typing_extensions import Protocol

from graphql import ExecutionResult, GraphQLSchema


class SchemaBindable(Protocol):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass  # pragma: no cover


# Note: this should be [Any, GraphQLResolveInfo, **kwargs],
# but this is not achieveable with python types yet:
# https://github.com/mirumee/ariadne/pull/79
Resolver = Callable[..., Any]
Subscriber = Callable[..., AsyncGenerator]
ErrorHandler = Callable[[ExecutionResult, bool], List[dict]]
ScalarOperation = Callable[[Any], Any]
