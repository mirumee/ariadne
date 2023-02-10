from inspect import isawaitable
from dataclasses import dataclass
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Collection,
    Dict,
    List,
    Optional,
    Sequence,
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

ContextValue = Union[
    Any,
    Callable[[Any], Any],  # TODO: remove in 0.19
    Callable[[Any, dict], Any],
]
RootValue = Union[
    Any,
    Callable[[Optional[Any], DocumentNode], Any],  # TODO: remove in 0.19
    Callable[[Optional[Any], Optional[str], Optional[dict], DocumentNode], Any],
]

QueryParser = Callable[[ContextValue, Dict[str, Any]], DocumentNode]

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

# Unspecific Middleware type in line what graphql-core expects.
# Could be made more specific in future versions but currently MyPY doesn't
# handle mixing __positional __args with **kwargs that we need.
# Callable[[Resolver, Any, GraphQLResolveInfo, KwArg(Any)], Any]
Middleware = Callable[..., Any]
MiddlewareList = Optional[Sequence[Middleware]]
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
    """Base class for async extensions.

    Subclasses of this this class should override default methods to run
    custom logic during Query execution.
    """

    def request_started(self, context: ContextValue) -> None:
        """Extension hook executed at request's start."""

    def request_finished(self, context: ContextValue) -> None:
        """Extension hook executed at request's end."""

    async def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        """Async extension hook wrapping field's value resolution.

        # Arguments

        `next_`: a `resolver` or next extension's `resolve` method.

        `obj`: a Python data structure to resolve value from.

        `info`: a `GraphQLResolveInfo` instance for executed resolver.

        `**kwargs`: extra arguments from GraphQL to pass to resolver.
        """
        result = next_(obj, info, **kwargs)
        if isawaitable(result):
            result = await result
        return result

    def has_errors(self, errors: List[GraphQLError], context: ContextValue) -> None:
        """Extension hook executed when GraphQL encountered errors."""

    def format(self, context: ContextValue) -> Optional[dict]:
        """Extension hook executed to retrieve extra data to include in result's
        `extensions` data."""


class ExtensionSync(Extension):
    """Base class for sync extensions, extends `Extension`.

    Subclasses of this this class should override default methods to run
    custom logic during Query execution.
    """

    def resolve(  # pylint: disable=invalid-overridden-method
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        """Sync extension hook wrapping field's value resolution.

        # Arguments

        `next_`: a `resolver` or next extension's `resolve` method.

        `obj`: a Python data structure to resolve value from.

        `info`: a `GraphQLResolveInfo` instance for executed resolver.

        `**kwargs`: extra arguments from GraphQL to pass to resolver.
        """
        return next_(obj, info, **kwargs)


@runtime_checkable
class SchemaBindable(Protocol):
    """Base class for bindable types.

    Subclasses should extend the `bind_to_schema` method with custom logic for
    populating an instance of GraphQL schema with Python logic and values.

    # Example

    Example `InputType` bindable that sets Python names for fields of GraphQL input:

    ```python
    from ariadne import SchemaBindable
    from graphql import GraphQLInputType

    class InputType(SchemaBindable):
        _name: str
        _fields: dict[str, str]

        def __init__(self, name: str, fields: dict[str, str] | None):
            self._name = name
            self._fields = fields or {}

        def set_field_out_name(self, field: str, out_name: str):
            self._fields[field] = out_name

        def bind_to_schema(self, schema: GraphQLSchema) -> None:
            graphql_type = schema.get_type(self._name)
            if not graphql_type:
                raise ValueError(
                    "Type %s is not defined in the schema" % self.name
                )
            if not isinstance(graphql_type, GraphQLInputType):
                raise ValueError(
                    "%s is defined in the schema, but it is instance of %s (expected %s)"
                    % (self.name, type(graphql_type).__name__, GraphQLInputType.__name__)
                )

            for field, out_name in self._fields.items():
                schema_field = graphql_type.fields.get(field)
                if not schema_field:
                    raise ValueError(
                        "Type %s does not define the %s field" % (self.name, field)
                    )

                schema_field.out_name = out_name
    ```

    Usage:

    ```python
    from ariadne import QueryType, make_executable_schema

    from .input_type import InputType
    from .users.models import User

    input_type = InputType(
        "UserInput",
        {
            "fullName": "full_name",
            "yearOfBirth": "year_of_birth",
        }
    )

    query_type = QueryType()

    @query_type.field("countUsers")
    def resolve_count_users(*_, input):
        qs = User.objects

        if input:
            if input["full_name"]:
                qs = qs.filter(full_name__ilike=input["full_name"])
            if input["year_of_birth"]:
                qs = qs.filter(dob__year=input["year_of_birth"])

        return qs.count()


    schema = make_executable_schema(
        \"\"\"
        type Query {
            countUsers(input: UserInput!): Int!
        }

        input UserInput {
            fullName: String
            yearOfBirth: Int
        }
        \"\"\",
        query_type,
        input_type,
    )
    ```
    """

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `SchemaBindable` instance to the instance of GraphQL schema."""


SubscriptionHandler = TypeVar("SubscriptionHandler")
SubscriptionHandlers = Union[
    Tuple[Type[SubscriptionHandler]], List[Type[SubscriptionHandler]]
]
