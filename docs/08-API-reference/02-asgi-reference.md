---
id: asgi-reference
title: ASGI reference
sidebar_label: ariadne.asgi
---

The `ariadne.asgi` package exports the `GraphQL` ASGI application:

## `GraphQL`

```python
class GraphQL:
    ...
```

ASGI application implementing the GraphQL server.

Can be used stand-alone or mounted within other ASGI application, for
example in Starlette or FastAPI.

### Constructor

```python
def __init__(
    self,
    schema: GraphQLSchema,
    *,
    context_value: Optional[ContextValue],
    root_value: Optional[RootValue],
    query_parser: Optional[QueryParser],
    query_validator: Optional[QueryValidator],
    validation_rules: Optional[ValidationRules],
    execute_get_queries: bool,
    debug: bool,
    introspection: bool,
    explorer: Optional[Explorer],
    logger: Union[None, str, Logger, LoggerAdapter],
    error_formatter: ErrorFormatter,
    execution_context_class: Optional[Type[ExecutionContext]],
    http_handler: Optional[GraphQLHTTPHandler],
    websocket_handler: Optional[GraphQLWebsocketHandler],
):
    ...
```

Initializes the ASGI app and it's http and websocket handlers.

#### Required arguments

`schema`: an instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to execute queries against.

#### Optional arguments

`context_value`: a [`ContextValue`](types-reference#contextvalue) to use by this server for context.
Defaults to `{"request": request}` dictionary where `request` is
an instance of `starlette.requests.Request`.

`root_value`: a [`RootValue`](types-reference#rootvalue) to use by this server for root value.
Defaults to `None`.

`query_parser`: a [`QueryParser`](types-reference#queryparser) to use by this server. Defaults to
`graphql.parse`.

`query_validator`: a `QueryValidator` to use by this server. Defaults to
`graphql.validate`.

`validation_rules`: a [`ValidationRules`](types-reference#validationrules) list or callable returning a
list of extra validation rules server should use to validate the
GraphQL queries. Defaults to `None`.

`execute_get_queries`: a `bool` that controls if `query` operations
sent using the `GET` method should be executed. Defaults to `False`.

`debug`: a `bool` controlling in server should run in debug mode or
not. Controls details included in error data returned to clients.
Defaults to `False`.

`introspection`: a `bool` controlling if server should allow the
GraphQL introspection queries. If `False`, introspection queries will
fail to pass the validation. Defaults to `True`.

[`explorer`](../Docs/explorers): an instance of [`Explorer`](../Docs/explorers) subclass to use when the server
receives an HTTP GET request. If not set, default GraphQL explorer
for your version of Ariadne is used.

`logger`: a `str` with name of logger or logger instance server
instance should use for logging errors. If not set, a logger named
`ariadne` is used.

`error_formatter`: an [`ErrorFormatter`](types-reference#errorformatter) this server should use to format
GraphQL errors returned to clients. If not set, default formatter
implemented by Ariadne is used.

`execution_context_class`: custom `ExecutionContext` type to use by
this server to execute the GraphQL queries. Defaults to standard
context type implemented by the `graphql`.

`http_handler`: an instance of [[`GraphQLHTTPHandler`](asgi-handlers-reference#graphqlhttphandler)](asgi-handlers-reference#graphqlhttphandler) class implementing
the HTTP requests handling logic for this server. If not set,
an instance of [[`GraphQLHTTPHandler`](asgi-handlers-reference#graphqlhttphandler)](asgi-handlers-reference#graphqlhttphandler) is used.

`websocket_handler`: an instance of [[`GraphQLWebsocketHandler`](asgi-handlers-reference#graphqlwebsockethandler)](asgi-handlers-reference#graphqlwebsockethandler) class
implementing the websocket connections handling logic for this server.
If not set, [`GraphQLWSHandler`](asgi-handlers-reference#graphqlwshandler) will be used, implementing older
version of GraphQL subscriptions protocol.

### Methods

#### `__call__`

```python
async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    ...
```

An entrypoint to the ASGI application.

Supports both HTTP and WebSocket connections.

##### Required arguments

`scope`: The [connection scope](https://asgi.readthedocs.io/en/latest/specs/main.html#connection-scope) information, a dictionary that contains
at least a type key specifying the protocol that is incoming.

`receive`: an awaitable callable that will yield a new event dictionary
when one is available.

`send`: an awaitable callable taking a single event dictionary as a
positional argument that will return once the send has been completed
or the connection has been closed.

Details about the arguments and their usage are described in the
ASGI specification:

https://asgi.readthedocs.io/en/latest/specs/main.html

#### `handle_request`

```python
async def handle_request(self, request: Request) -> Response:
    ...
```

Shortcut for `graphql_app.http_handler.handle_request(...)`.

#### `handle_websocket`

```python
async def handle_websocket(self, websocket: Any) -> Awaitable[Any]:
    ...
```

Shortcut for `graphql_app.websocket_handler.handle_websocket(...)`.

---

`ariadne.asgi` package also reexports following names:

- `Extensions`
- `MiddlewareList`
- `Middlewares`
- `OnComplete`
- `OnConnect`
- `OnDisconnect`
- `OnOperation`
- `Operation`
- `WebSocketConnectionError`
