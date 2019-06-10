from inspect import isawaitable
from typing import Any, AsyncGenerator, Callable, List, Optional, Tuple, Union
from typing_extensions import Protocol

from graphql import DocumentNode, ExecutionResult, GraphQLError, GraphQLSchema


class Extension(Protocol):
    def parsing_did_start(self, query):
        pass  # pragma: no cover

    def parsing_did_end(self):
        pass  # pragma: no cover

    def validation_did_start(self):
        pass  # pragma: no cover

    def validation_did_end(self):
        pass  # pragma: no cover

    def execution_did_start(self):
        pass  # pragma: no cover
    
    def execution_did_end(self):
        pass  # pragma: no cover

    async def resolve(self, next_, parent, info, **kwargs):
        result = next_(parent, info, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    def will_send_response(self, result, context=None):
        return result  # pragma: no cover


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
