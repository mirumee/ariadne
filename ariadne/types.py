from inspect import isawaitable
from typing import Any, AsyncGenerator, Callable, List, Optional, Tuple, Union
from typing_extensions import Protocol

from graphql import DocumentNode, ExecutionResult, GraphQLError, GraphQLSchema


class Extension(Protocol):
    def request_started(self, context):
        pass  # pragma: no cover

    def request_finished(self, context, error=None):
        pass  # pragma: no cover

    def parsing_started(self, query):
        pass

    def parsing_finished(self, query, error=None):
        pass

    def validation_started(self, context):
        pass  # pragma: no cover

    def validation_finished(self, context, error=None):
        pass  # pragma: no cover

    def execution_started(self, context):
        pass  # pragma: no cover

    def execution_finished(self, context, error=None):
        pass  # pragma: no cover

    async def resolve(self, next_, parent, info, **kwargs):
        result = next_(parent, info, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    def has_errors(self, errors):
        pass  # pragma: no cover

    def format(self):
        pass  # pragma: no cover


class SchemaBindable(Protocol):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass  # pragma: no cover


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
