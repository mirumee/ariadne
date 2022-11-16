from inspect import isawaitable
from dataclasses import dataclass
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Collection,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    TypeVar,
)
from typing_extensions import Protocol, runtime_checkable

from graphql import (
    DocumentNode,
    ExecutionResult,
    GraphQLError,
    GraphQLResolveInfo,
    GraphQLSchema,
)
from graphql.validation.rules import ASTValidationRule
from graphql.execution import Middleware

from starlette.websockets import WebSocket


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

ValidationRules = Union[
    Collection[Type[ASTValidationRule]],
    Callable[
        [Optional[Any], DocumentNode, dict],
        Optional[Collection[Type[ASTValidationRule]]],
    ],
]

ExtensionList = Optional[List[Union[Type["Extension"], Callable[[], "Extension"]]]]


Extensions = Union[
    Callable[[Any, Optional[ContextValue]], ExtensionList], ExtensionList
]
MiddlewareList = Optional[List[Middleware]]
Middlewares = Union[
    Callable[[Any, Optional[ContextValue]], MiddlewareList], MiddlewareList
]


@dataclass
class Operation:
    id: str
    name: Optional[str]
    generator: AsyncGenerator


OnConnect = Callable[[WebSocket, Any], Any]
OnDisconnect = Callable[[WebSocket], Any]
OnOperation = Callable[[WebSocket, Operation], Any]
OnComplete = Callable[[WebSocket, Operation], Any]


class WebSocketConnectionError(Exception):
    """Special error class enabling custom error reporting for on_connect"""

    def __init__(self, payload: Optional[Union[dict, str]] = None) -> None:
        if isinstance(payload, dict):
            self.payload = payload
        elif payload:
            self.payload = {"message": str(payload)}
        else:
            self.payload = {"message": "Unexpected error has occurred."}


@runtime_checkable
class Extension(Protocol):
    def request_started(self, context: ContextValue):
        pass  # pragma: no cover

    def request_finished(self, context: ContextValue):
        pass  # pragma: no cover

    async def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):
        result = next_(obj, info, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    def has_errors(self, errors: List[GraphQLError], context: ContextValue):
        pass  # pragma: no cover

    def format(self, context: ContextValue) -> Optional[dict]:
        pass  # pragma: no cover


class ExtensionSync(Extension):
    def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ):  # pylint: disable=invalid-overridden-method
        return next_(obj, info, **kwargs)


@runtime_checkable
class SchemaBindable(Protocol):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass  # pragma: no cover


SubscriptionHandler = TypeVar("SubscriptionHandler")
SubscriptionHandlers = Union[
    Tuple[Type[SubscriptionHandler]], List[Type[SubscriptionHandler]]
]
