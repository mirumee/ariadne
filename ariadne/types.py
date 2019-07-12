from inspect import isawaitable
from typing import Any, AsyncGenerator, Callable, List, Optional, Tuple, Union
from typing_extensions import Protocol

from graphql import (
    DocumentNode,
    ExecutionResult,
    GraphQLError,
    GraphQLResolveInfo,
    GraphQLSchema,
)

# Note: this should be [Any, GraphQLResolveInfo, **kwargs],
# but this is not achieveable with python types yet:
# https://github.com/mirumee/ariadne/pull/79
Resolver = Callable[..., Any]
GraphQLResult = Tuple[bool, dict]
SubscriptionResult = Tuple[
    bool, Union[List[dict], AsyncGenerator[ExecutionResult, None]]
]
Subscriber = Callable[..., AsyncGenerator]
ErrorFormatter = Callable[[GraphQLError, bool], dict]

ContextValue = Union[Any, Callable[[Any], Any]]
RootValue = Union[Any, Callable[[Optional[Any], DocumentNode], Any]]


class Extension(Protocol):
    def request_started(self, context: ContextValue):
        pass  # pragma: no cover

    def request_finished(
        self, context: ContextValue, error: Optional[Exception] = None
    ):
        pass  # pragma: no cover

    async def resolve(
        self, next_: Resolver, parent: Any, info: GraphQLResolveInfo, **kwargs
    ):
        result = next_(parent, info, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    def has_errors(self, errors: List[GraphQLError]):
        pass  # pragma: no cover

    def format(self) -> dict:
        return {}  # pragma: no cover


class SchemaBindable(Protocol):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass  # pragma: no cover
