---
id: asgi-handlers-reference
title: ASGI handlers reference
sidebar_label: ariadne.asgi.handlers
---

The `ariadne.asgi.handlers` package exports following 
ASGI request handlers:



## `GraphQLHTTPHandler`

```python
class GraphQLHTTPHandler(GraphQLHttpHandlerBase):
    ...
```

Default ASGI handler for HTTP requests.

Supports the `Query` and `Mutation` operations.


### Constructor

```python
def __init__(
    self,
    extensions: Optional[Extensions] = None,
    middleware: Optional[Middlewares] = None,
    middleware_manager_class: Optional[Type[MiddlewareManager]] = None,
):
    ...
```

Initializes the HTTP handler.


#### Optional arguments

[`extensions`](types-reference#extensions): an [`Extensions`](types-reference#extensions) list or callable returning a
list of extensions server should use during query execution. Defaults
to no extensions.

`middleware`: a [`Middlewares`](types-reference#middlewares) list or callable returning a list of
middlewares server should use during query execution. Defaults to no
middlewares.

`middleware_manager_class`: a `MiddlewareManager` type or subclass to
use for combining provided middlewares into single wrapper for resolvers
by the server. Defaults to `graphql.MiddlewareManager`. Is only used
if [`extensions`](types-reference#extensions) or `middleware` options are set.


### Methods

#### `handle`

```python
async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
    ...
```

An entrypoint for the GraphQL HTTP handler.

This method is called by the Ariadne ASGI GraphQL application to execute
queries done using the HTTP protocol.

It creates the `starlette.requests.Request` instance, calls
`handle_request` method with it, then sends response back to the client.


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

Handle GraphQL request and return response for the client.

Is called by the `handle` method and `handle_request` method of the
ASGI GraphQL application.

Handles three HTTP methods:

`GET`: returns GraphQL explorer or 405 error response if explorer or
introspection is disabled.

`POST`: executes the GraphQL query from either `application/json` or
`multipart/form-data` requests.

`OPTIONS`: returns supported HTTP methods.

Returns Starlette's `Response` instance, which is also works in FastAPI.


##### Required arguments:

`request`: the `Request` instance from Starlette or FastAPI.


#### `render_explorer`

```python
async def render_explorer(self, request: Request, explorer: Explorer) -> Response:
    ...
```

Return a HTML response with GraphQL explorer.


##### Required arguments:

`request`: the `Request` instance from Starlette or FastAPI.

[`explorer`](../Docs/explorers): an [`Explorer`](../Docs/explorers) instance that implements the
`html(request: Request)` method which returns either the `str` with HTML
or `None`. If explorer returns `None`, `405` method not allowed response
is returned instead.


#### `graphql_http_server`

```python
async def graphql_http_server(self, request: Request) -> Response:
    ...
```

Handles the HTTP request with GraphQL query.

Extracts GraphQL query data from requests and then executes it using
the `execute_graphql_query` method.

Returns the JSON response from Sta

If request's data was invalid or missing, plaintext response with
error message and 400 status code is returned instead.


##### Required arguments:

`request`: the `Request` instance from Starlette or FastAPI.


#### `extract_data_from_request`

```python
async def extract_data_from_request(self, request: Request) -> Union[dict, list]:
    ...
```

Extracts GraphQL request data from request.

Returns a `dict` or `list` with GraphQL query data that was not yet validated.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.


#### `extract_data_from_json_request`

```python
async def extract_data_from_json_request(self, request: Request) -> dict:
    ...
```

Extracts GraphQL data from JSON request.

Returns a `dict` with GraphQL query data that was not yet validated.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.


#### `extract_data_from_multipart_request`

```python
async def extract_data_from_multipart_request(
    self,
    request: Request,
) -> Union[dict, list]:
    ...
```

Extracts GraphQL data from `multipart/form-data` request.

Returns an unvalidated `dict` or `list` with GraphQL query data.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.


#### `extract_data_from_get_request`

```python
def extract_data_from_get_request(self, request: Request) -> dict:
    ...
```

Extracts GraphQL data from GET request's querystring.

Returns a `dict` with GraphQL query data that was not yet validated.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.


#### `execute_graphql_query`

```python
async def execute_graphql_query(
    self,
    request: Any,
    data: Any,
    *,
    context_value: Any,
    query_document: Optional[DocumentNode],
) -> GraphQLResult:
    ...
```

Executes GraphQL query from `request` and returns [`GraphQLResult`](types-reference#graphqlresult).

Creates GraphQL [`ContextValue`](types-reference#contextvalue), initializes extensions and middlewares,
then runs the `graphql` function from Ariadne to execute the query.


##### Requires arguments

`request`: the `Request` instance from Starlette or FastAPI.

`data`: a GraphQL data.


##### Optional arguments

`context_value`: a [`ContextValue`](types-reference#contextvalue) for this request.

`query_document`: an already parsed GraphQL query. Setting this option
will prevent `graphql` from parsing `query` string from `data` second time.


#### `get_extensions_for_request`

```python
async def get_extensions_for_request(
    self,
    request: Any,
    context: Optional[ContextValue],
) -> ExtensionList:
    ...
```

Returns extensions to use when handling the GraphQL request.

Returns [`ExtensionList`](types-reference#extensionlist), a list of extensions to use or `None`.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.

`context`: a [`ContextValue`](types-reference#contextvalue) for this request.


#### `get_middleware_for_request`

```python
async def get_middleware_for_request(
    self,
    request: Any,
    context: Optional[ContextValue],
) -> MiddlewareList:
    ...
```

Returns GraphQL middlewares to use when handling the GraphQL request.

Returns [`MiddlewareList`](types-reference#middlewarelist), a list of middlewares to use or `None`.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.

`context`: a [`ContextValue`](types-reference#contextvalue) for this request.


#### `create_json_response`

```python
async def create_json_response(
    self,
    request: Request,
    result: dict,
    success: bool,
) -> Response:
    ...
```

Creates JSON response from GraphQL's query result.

Returns Starlette's `JSONResponse` instance that's also compatible
with FastAPI. If `success` is `True`, response's status code is 200.
Status code 400 is used otherwise.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.

`result`: a JSON-serializable `dict` with query result.

`success`: a `bool` specifying if


#### `handle_not_allowed_method`

```python
def handle_not_allowed_method(self, request: Request) -> None:
    ...
```

Handles request for unsupported HTTP method.

Returns 200 response for `OPTIONS` request and 405 response for other
methods. All responses have empty body.


##### Required arguments

`request`: the `Request` instance from Starlette or FastAPI.


- - - - -


## `GraphQLHandler`

```python
class GraphQLHandler(ABC):
    ...
```

Base class for ASGI connection handlers.


### Constructor

```python
def __init__(self):
    ...
```

Initialize the handler instance with empty configuration.


### Methods

#### `handle`

```python
async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
    ...
```

An entrypoint for the ASGI connection handler.

This method is called by Ariadne ASGI GraphQL application. Subclasses
should replace it with custom implementation.


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


#### `configure`

```python
def configure(
    self,
    schema: GraphQLSchema,
    context_value: Optional[ContextValue] = None,
    root_value: Optional[RootValue] = None,
    query_parser: Optional[QueryParser] = None,
    query_validator: Optional[QueryValidator] = None,
    validation_rules: Optional[ValidationRules] = None,
    execute_get_queries: bool = False,
    debug: bool = False,
    introspection: bool = True,
    explorer: Optional[Explorer] = None,
    logger: Union[None, str, Logger, LoggerAdapter] = None,
    error_formatter: ErrorFormatter = format_error,
    execution_context_class: Optional[Type[ExecutionContext]] = None,
) -> None:
    ...
```

Configures the handler with options from the ASGI application.

Called by Ariadne ASGI GraphQL application as part of its
initialization, propagating the configuration to it's handlers.


#### `get_context_for_request`

```python
async def get_context_for_request(self, request: Any, data: dict) -> Any:
    ...
```

Returns GraphQL context value for ASGI connection.

Resolves final context value from the [`ContextValue`](types-reference#contextvalue) value passed to
`context_value` option. If `context_value` is None, sets default context
value instead, which is a `dict` with single `request` key that contains
either `starlette.requests.Request` instance or
`starlette.websockets.WebSocket` instance.


##### Required arguments

`request`: an instance of ASGI connection. It's type depends on handler.

`data`: a GraphQL data from connection.


- - - - -


## `GraphQLHttpHandlerBase`

```python
class GraphQLHttpHandlerBase(GraphQLHandler):
    ...
```

Base class for ASGI HTTP connection handlers.


### Methods

#### `handle_request`

```python
async def handle_request(self, request: Any) -> Any:
    ...
```

Abstract method for handling the request.

Should return valid ASGI response.


#### `execute_graphql_query`

```python
async def execute_graphql_query(
    self,
    request: Any,
    data: Any,
    *,
    context_value: Optional[Any],
    query_document: Optional[DocumentNode],
) -> GraphQLResult:
    ...
```

Abstract method for GraphQL query execution.


- - - - -


## `GraphQLTransportWSHandler`

```python
class GraphQLTransportWSHandler(GraphQLWebsocketHandler):
    ...
```

Implementation of the (newer) graphql-transport-ws subprotocol
from the graphql-ws library.

For more details see it's GH page:

https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md


### Constructor

```python
def __init__(
    self,
    *args,
    connection_init_wait_timeout: timedelta,
    **kwargs,
):
    ...
```

Initializes the websocket handler.


#### Optional arguments

`connection_init_wait_timeout`: a `timedelta` with timeout for new
websocket connections before first message is received. Defaults to
60 seconds.


### Methods

#### `handle`

```python
async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
    ...
```

An entrypoint for the GraphQL WebSocket handler.

This method is called by the Ariadne ASGI GraphQL application to handle
the websocket connections.

It creates the `starlette.websockets.WebSocket` instance and calls
`handle_websocket` method with it.


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


#### `handle_websocket`

```python
async def handle_websocket(self, websocket: WebSocket) -> None:
    ...
```

Handle GraphQL the WebSocket connection.

Is called by the `handle` method and `handle_websocket` method of the
ASGI GraphQL application.


##### Required arguments:

`websocket`: the `WebSocket` instance from Starlette or FastAPI.


#### `handle_connection_init_timeout`

```python
async def handle_connection_init_timeout(
    self,
    websocket: WebSocket,
    client_context: ClientContext,
) -> None:
    ...
```


#### `handle_websocket_message`

```python
async def handle_websocket_message(
    self,
    websocket: WebSocket,
    message: dict,
    client_context: ClientContext,
) -> None:
    ...
```

Handles new message from websocket connection.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`message`: a `dict` with message payload.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `handle_websocket_connection_init_message`

```python
async def handle_websocket_connection_init_message(
    self,
    websocket: WebSocket,
    message: dict,
    client_context: ClientContext,
) -> None:
    ...
```

Handles `connection_init` websocket message.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`message`: a `dict` with message payload.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `handle_websocket_ping_message`

```python
async def handle_websocket_ping_message(
    self,
    websocket: WebSocket,
    client_context: ClientContext,
) -> None:
    ...
```

Handles `ping` websocket message, answering with `pong` message.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `handle_websocket_pong_message`

```python
async def handle_websocket_pong_message(
    self,
    websocket: WebSocket,
    client_context: ClientContext,
) -> None:
    ...
```

Handles `pong` websocket message.

Unlike `ping` message, `pong` is unidirectional heartbeat sent by the
client to the server. It doesn't require a result.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `handle_websocket_complete_message`

```python
async def handle_websocket_complete_message(
    self,
    websocket: WebSocket,
    operation_id: str,
    client_context: ClientContext,
) -> None:
    ...
```

Handles `complete` websocket message.

`complete` message tells the GraphQL server to stop sending events for
GraphQL operation specified in the message


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`operation_id`: a `str` with id of operation that should be stopped.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `handle_websocket_subscribe`

```python
async def handle_websocket_subscribe(
    self,
    websocket: WebSocket,
    data: Any,
    operation_id: str,
    client_context: ClientContext,
) -> None:
    ...
```

Handles `subscribe` websocket message.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`data`: any data from `subscribe` message.

`operation_id`: a `str` with id of new subscribe operation.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `handle_websocket_invalid_type`

```python
async def handle_websocket_invalid_type(self, websocket: WebSocket) -> None:
    ...
```

Handles unsupported or invalid websocket message.

Closes open websocket connection with error code `4400`.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.


#### `handle_on_complete`

```python
async def handle_on_complete(
    self,
    websocket: WebSocket,
    operation: Operation,
) -> None:
    ...
```

Handles completed websocket operation.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

[`operation`](types-reference#operation): a completed [`Operation`](types-reference#operation).


#### `stop_websocket_operation`

```python
async def stop_websocket_operation(
    self,
    websocket: WebSocket,
    operation_id: str,
    client_context: ClientContext,
) -> None:
    ...
```

Stops specified GraphQL operation for given connection and context.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`operation_id`: a `str` with id of operation to stop.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


#### `observe_async_results`

```python
async def observe_async_results(
    self,
    websocket: WebSocket,
    results_producer: AsyncGenerator,
    operation_id: str,
    client_context: ClientContext,
) -> None:
    ...
```

Converts results from Ariadne's `subscribe` generator into websocket
messages it next sends to the client.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`results_producer`: the `AsyncGenerator` returned from Ariadne's
`subscribe` function.

`operation_id`: a `str` with id of operation.

`client_context`: a `ClientContext` object with extra state of current
websocket connection.


- - - - -


## `GraphQLWSHandler`

```python
class GraphQLWSHandler(GraphQLWebsocketHandler):
    ...
```

Implementation of the (older) graphql-ws subprotocol from the
subscriptions-transport-ws library.

For more details see it's GH page:

https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md


### Constructor

```python
def __init__(self, *args, keepalive: Optional[float], **kwargs):
    ...
```

Initializes the websocket handler.


#### Optional arguments

`keepalive`: a `float` with time frequency for sending the keep-alive
messages to clients with open websocket connections. `1.0` is 1 second.
If set to `None` or `0`, no keep-alive messages are sent.
Defaults to `None`.


### Methods

#### `handle`

```python
async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
    ...
```

An entrypoint for the GraphQL WebSocket handler.

This method is called by the Ariadne ASGI GraphQL application to handle
the websocket connections.

It creates the `starlette.websockets.WebSocket` instance and calls
`handle_websocket` method with it.


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


#### `handle_websocket`

```python
async def handle_websocket(self, websocket: WebSocket) -> None:
    ...
```

Handle GraphQL the WebSocket connection.

Is called by the `handle` method and `handle_websocket` method of the
ASGI GraphQL application.


##### Required arguments:

`websocket`: the `WebSocket` instance from Starlette or FastAPI.


#### `handle_websocket_message`

```python
async def handle_websocket_message(
    self,
    websocket: WebSocket,
    message: dict,
    operations: Dict[str, Operation],
) -> None:
    ...
```

Handles new message from websocket connection.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`message`: a `dict` with message payload.

`operations`: a `dict` with currently active GraphQL operations.


#### `process_single_message`

```python
async def process_single_message(
    self,
    websocket: WebSocket,
    data: Any,
    operation_id: str,
    operations: Dict[str, Operation],
) -> None:
    ...
```

Processes websocket message containing new GraphQL operation.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`data`: a `dict` with message's payload.

`operation_id`: a `str` with an ID of new operation.

`operations`: a `dict` with currently active GraphQL operations.


#### `handle_websocket_connection_init_message`

```python
async def handle_websocket_connection_init_message(
    self,
    websocket: WebSocket,
    message: dict,
) -> None:
    ...
```

Handles `connection_init` websocket message.

Initializes new websocket instance.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`message`: a `dict` with message's payload.


#### `handle_websocket_connection_terminate_message`

```python
async def handle_websocket_connection_terminate_message(
    self,
    websocket: WebSocket,
) -> None:
    ...
```

Handles `terminate` websocket message.

Closes open websocket connection.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.


#### `keep_websocket_alive`

```python
async def keep_websocket_alive(self, websocket: WebSocket) -> None:
    ...
```


#### `start_websocket_operation`

```python
async def start_websocket_operation(
    self,
    websocket: WebSocket,
    data: Any,
    context_value: Any,
    query_document: DocumentNode,
    operation_id: str,
    operations: Dict[str, Operation],
) -> None:
    ...
```


#### `stop_websocket_operation`

```python
async def stop_websocket_operation(
    self,
    websocket: WebSocket,
    operation: Operation,
) -> None:
    ...
```

Stops specified GraphQL operation for given connection.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

[`operation`](types-reference#operation): an [`Operation`](types-reference#operation) to stop.


#### `observe_async_results`

```python
async def observe_async_results(
    self,
    websocket: WebSocket,
    results: AsyncGenerator,
    operation_id: str,
) -> None:
    ...
```

Converts results from Ariadne's `subscribe` generator into websocket
messages it next sends to the client.


##### Required arguments

`websocket`: the `WebSocket` instance from Starlette or FastAPI.

`results`: the `AsyncGenerator` returned from Ariadne's
`subscribe` function.

`operation_id`: a `str` with id of operation.


- - - - -


## `GraphQLWebsocketHandler`

```python
class GraphQLWebsocketHandler(GraphQLHandler):
    ...
```

Base class for ASGI websocket connection handlers.


### Constructor

```python
def __init__(
    self,
    on_connect: Optional[OnConnect] = None,
    on_disconnect: Optional[OnDisconnect] = None,
    on_operation: Optional[OnOperation] = None,
    on_complete: Optional[OnComplete] = None,
):
    ...
```

Initialize websocket handler with optional options specific to it.


#### Optional arguments:

`on_connect`: an [`OnConnect`](types-reference#onconnect) callback used on new websocket connection.

`on_disconnect`: an [`OnDisconnect`](types-reference#ondisconnect) callback used when existing
websocket connection is closed.

`on_operation`: an [`OnOperation`](types-reference#onoperation) callback, used when new GraphQL
operation is received from websocket connection.

`on_complete`: an [`OnComplete`](types-reference#oncomplete) callback, used when GraphQL operation
received over the websocket connection was completed.


### Methods

#### `handle_websocket`

```python
async def handle_websocket(self, websocket: Any) -> None:
    ...
```

Abstract method for handling the websocket connection.


#### `configure`

```python
def configure(
    self,
    *args,
    http_handler: Optional[GraphQLHttpHandlerBase],
    **kwargs,
) -> None:
    ...
```

Configures the handler with options from the ASGI application.

Called by Ariadne ASGI GraphQL application as part of its
initialization, propagating the configuration to it's handlers.


##### Optional arguments

`http_handler`: the `GraphQLHttpHandlerBase` subclass instance to use
to execute the `Query` and `Mutation` operations made over the
websocket connections.