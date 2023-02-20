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

__all__ = [
    "Resolver",
    "GraphQLResult",
    "SubscriptionResult",
    "Subscriber",
    "ErrorFormatter",
    "ContextValue",
    "RootValue",
    "QueryParser",
    "ValidationRules",
    "ExtensionList",
    "Extensions",
    "Middleware",
    "MiddlewareList",
    "Middlewares",
    "Operation",
    "OnConnect",
    "OnDisconnect",
    "OnOperation",
    "OnComplete",
    "WebSocketConnectionError",
    "Extension",
    "ExtensionSync",
    "SchemaBindable",
]


# Note: this should be [Any, GraphQLResolveInfo, **kwargs],
# but this is not achieveable with python types yet:
# https://github.com/mirumee/ariadne/pull/79
"""Type for resolver functions.

Due to limitations in Mypy this type is unspecific. More accurate type is:

```python
Resolver = Callable[[Any, GraphQLResolveInfo, KwArg[Any]], Any]
```

Each resolver is called with two positional arguments and any number of keyword 
arguments:

`Any`: a Python representation of GraphQL type to resolve value from.

`GraphQLResolveInfo`: an instance of GraphQL object holding data about currently 
executed GraphQL field, and `context` attribute.

`KwArg[Any]`: if currently executed GraphQL field has any arguments, their 
values will be passed as keyword arguments.
"""
Resolver = Callable[..., Any]

"""Result type for `graphql` and `graphql_sync` functions.

It's a tuple of two elements:

`bool`: `True` when query was executed successfully (without any errors), `False` otherwise.

`dict`: JSON-serializable query result.
"""
GraphQLResult = Tuple[bool, dict]

"""Result type for `subscribe` function.

It's a tuple of two elements:

`bool`: `True` when query was executed successfully (without any errors), `False` otherwise.

`dict or generator`: JSON-serializable query result or asynchronous generator with 
subscription's results. Depends if query was success or not.
"""
SubscriptionResult = Tuple[
    bool, Union[List[dict], AsyncGenerator[ExecutionResult, None]]
]

"""Type for subscription source functions.

Due to limitations in Mypy this type is unspecific. More accurate type is:

```python
Subscriber = Callable[[Any, GraphQLResolveInfo, KwArg[Any]], AsyncGenerator]
```

Receives same arguments as `Resolver`.
"""
Subscriber = Callable[..., AsyncGenerator]

"""Type for custom error formatters.

Error formatter is a function called by Ariadne to convert `GraphQLError` 
instance into JSON-serializable dict to return to client.

It receives two arguments:

`GraphQLError`: an error to serialize.

`bool`: a `debug` flag, which tells the formatter if it should (`True`) or 
shouldn't (`False`) include debugging information.
"""
ErrorFormatter = Callable[[GraphQLError, bool], dict]

"""Type for `context_value` option of GraphQL servers.

Context value is accessible in GraphQL resolvers as `context` attribute of 
second argument:

```python
def resolve_example(_, info: GraphQLResolveInfo):
    info.context  # Do something with context
```

# Default context

Default context value passed to resolvers by Ariadne is a dictionary with single 
key, `request`, which contains the HTTP framework specific representation of HTTP 
request:

```python
def resolve_example(_, info: GraphQLResolveInfo):
    request = info.context["request"]  # Get request from context
```

# Dynamic context value

If context value is a callable, it will be evaluated at the beginning of query 
execution.

It's called with two arguments:

`request`: an representation of HTTP request specific to the framework used.

`data`: an _unvalidated_ JSON which may be a valid GraphQL request payload.

Callable can return any value which will then be passed to resolvers. Some 
implementations (like `ariadne.asgi.GraphQL`) support this callable being 
asynchronous.

Here's an example callable that retrieves application settings from database, 
then uses them together with request to retrieve authenticated user. Finally 
it exposes all three of those to GraphQL resolvers:

```python
from ariadne.asgi import GraphQL
from starlette.requests import Request

from .auth import get_authenticated_user
from .settings import get_db_settings
from .schema import schema

async def get_context_value(request: Request, _):
    settings = await get_db_settings()
    user = await get_authenticated_user(request, settings)

    return {
        "request"; request,
        "settings": settings,
        "user": user,
    }

graphql_app = GraphQL(
    schema,
    context_value=get_context_value,
)
```
"""
ContextValue = Union[
    Any,
    Callable[[Any], Any],  # TODO: remove in 0.20
    Callable[[Any, dict], Any],
]

"""Type for `root_value` option of GraphQL servers.

"Root value" is a value passed to root resolvers (resolvers set on `Query`, 
`Mutation` and `Subscription` fields) as first argument.

# Default root value

Ariadne doesn't define root value by default. First argument of root resolvers 
is `None`.

# Dynamic root value

If root value is a callable, it will be evaluated at the beginning of query 
handling. It's called with four arguments:

`context_value`: a context value specific to this GraphQL server.

`operation_name`: a `str` with name of operation to execute (or `None`).

`variables`: a `dict` with variables to pass to query's resolvers (or `None`).

`document`: a `DocumentNode` with parsed GraphQL query.

Callable can return any value which then will be passed to root resolvers. 
Some implementations (like `ariadne.asgi.GraphQL`) support this callable being 
asynchronous.
"""
RootValue = Union[
    Any,
    Callable[[Optional[Any], DocumentNode], Any],  # TODO: remove in 0.20
    Callable[[Optional[Any], Optional[str], Optional[dict], DocumentNode], Any],
]

"""Type of `query_parser` option of GraphQL servers.

Enables customization of server's GraphQL parsing logic. If not set or `None`, 
default parser is used instead.

# Default query parser

Default query parser used by Ariadne is `parse` function from the `graphql` 
package.

# Custom parser

Custom parser is a function or callable accepting two arguments:

`context_value`: a context value specific to this GraphQL server.

`data`: a `dict` with validated GraphQL request data (contains `query` string, 
optionally also has `operationName` string or `variables` dictionary).

Parser is required to return `DocumentNode` with parsed query or raise 
`GraphQLError` when query is data invalid .

Asynchronous parsers are __not__ supported.

# Example parser

Below code defines custom parser that discards query string altogether, using 
predefined queries instead:

```python
from graphql import GraphQLError, parse


class AllowedQueriesParser:
    def __init__(self):
        self._queries = {}

    def __call__(self, _, data):
        operation_name = data.get("operationName")
        if not operation_name:
            raise GraphQLError(
                "Explicit 'operationName' is required by the server."
            )
        if operation_name not in self._queries:
            raise GraphQLError(
                f"Operation 'operation_name' is not supported by the server."
            )

        return self._queries[operation_name]

    def add_query(self, operation_name: str, query: str):
        self._queries[operation_name] = parse(query)


allowed_queries_parser = AllowedQueriesParser()

allowed_queries_parser.add_query(
    "GetUsers",
    \"\"\"
    query GetUsers {
        users {
            id
            name
        }
    }
    \"\"\"
)
```
"""
QueryParser = Callable[[ContextValue, Dict[str, Any]], DocumentNode]

"""Type of `validation_rules` option of GraphQL servers.

Enables extending of server's query validation logic.

Is either a callable that should return list of validation rules to use for 
GraphQL request, or list of validation rules.

Callable is evaluated with three arguments:

`Optional[Any]`: a context value for this request, or `None`.

`DocumentNode`: a `document` with parsed GraphQL query.

`dict`: a GraphQL request's data.
"""
ValidationRules = Union[
    Collection[Type[ASTValidationRule]],
    Callable[
        [Optional[Any], DocumentNode, dict],
        Optional[Collection[Type[ASTValidationRule]]],
    ],
]

"""List of extensions to use during GraphQL query execution."""
ExtensionList = Optional[List[Union[Type["Extension"], Callable[[], "Extension"]]]]

"""Type of `extensions` option of GraphQL servers.

It's either a list of extensions (see `ExtensionList`), or callable that 
returns this list.

Callable is evaluated with two arguments:

`Any`: the HTTP framework specific representation of HTTP request.

`Optional[ContextValue]`: a context value for this request, or `None`.
"""
Extensions = Union[
    Callable[[Any, Optional[ContextValue]], ExtensionList], ExtensionList
]

# Unspecific Middleware type in line what graphql-core expects.
# Could be made more specific in future versions but currently MyPY doesn't
# handle mixing __positional __args with **kwargs that we need.
# Callable[[Resolver, Any, GraphQLResolveInfo, KwArg(Any)], Any]
"""GraphQL middleware.

Due to limitations in Mypy this type is unspecific. More accurate type is:

```python
Middleware = Callable[[Resolver, Any, GraphQLResolveInfo, KwArg[Any]], Any]
```

Each middleware is called with three positional arguments and any number of 
keyword arguments:

`Resolver`: executed field's resolver or next GraphQL middleware.

`Any`: a Python representation of GraphQL type to resolve value from.

`GraphQLResolveInfo`: an instance of GraphQL object holding data about currently 
executed GraphQL field, and `context` attribute.

`KwArg[Any]`: if currently executed GraphQL field has any arguments, their 
values will be passed as keyword arguments.
"""
Middleware = Callable[..., Any]

"""List of middlewares to use during GraphQL query execution."""
MiddlewareList = Optional[Sequence[Middleware]]

"""Type of `middleware` option of GraphQL servers.

It's either a list of middleware (see `MiddlewareList`), or callable that 
returns this list.

Callable is evaluated with two arguments:

`Any`: the HTTP framework specific representation of HTTP request.

`Optional[ContextValue]`: a context value for this request, or `None`.
"""
Middlewares = Union[
    Callable[[Any, Optional[ContextValue]], MiddlewareList], MiddlewareList
]


@dataclass
class Operation:
    """Dataclass representing single active GraphQL operation."""

    id: str
    name: Optional[str]
    generator: AsyncGenerator


"""Type of `on_connect` option of GraphQL websocket servers.

Callback function evaluated when new websocket connection was established. 
Usually used to update connection's `scope` with contents of initial message.

Called with two arguments:

`WebSocket`: the HTTP framework specific representation of websocket connection.

`Any`: a data sent in WebSocket message.
"""
OnConnect = Callable[[WebSocket, Any], Any]

"""Type of `on_disconnect` option of GraphQL websocket servers.

Callback function evaluated when websocket connection is closed.

Called with one arguments:

`WebSocket`: the HTTP framework specific representation of websocket connection.
"""
OnDisconnect = Callable[[WebSocket], Any]

"""Type of `on_operation` option of GraphQL websocket servers.

Callback function evaluated when individual GraphQL subscription is initiated.

Called with two arguments:

`WebSocket`: the HTTP framework specific representation of websocket connection.

`Operation`: an object with initiated subscription's data.
"""
OnOperation = Callable[[WebSocket, Operation], Any]

"""Type of `on_complete` option of GraphQL websocket servers.

Callback function evaluated when individual GraphQL subscription is completed.

Called with two arguments:

`WebSocket`: the HTTP framework specific representation of websocket connection.

`Operation`: an object with closed subscription's data.
"""
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
