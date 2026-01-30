---
id: wsgi-reference
title: WSGI reference
sidebar_label: ariadne.wsgi
---

The `ariadne.wsgi` module exports the WSGI application and middleware:



## `GraphQL`

```python
class GraphQL:
    ...
```

WSGI application implementing the GraphQL server.


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
    debug: bool,
    introspection: bool,
    explorer: Optional[Explorer],
    logger: Optional[str],
    error_formatter: ErrorFormatter,
    execute_get_queries: bool,
    extensions: Optional[Extensions],
    middleware: Optional[Middlewares],
    middleware_manager_class: Optional[Type[MiddlewareManager]],
    execution_context_class: Optional[Type[ExecutionContext]],
):
    ...
```

Initializes the WSGI app.


#### Required arguments

`schema`: an instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to execute queries against.


#### Optional arguments

`context_value`: a [`ContextValue`](types-reference#contextvalue) to use by this server for context.
Defaults to `{"request": request}` dictionary where `request` is
an WSGI environment dictionary.

`root_value`: a [`RootValue`](types-reference#rootvalue) to use by this server for root value.
Defaults to `None`.

`query_parser`: a [`QueryParser`](types-reference#queryparser) to use by this server. Defaults to
`graphql.parse`.

`query_validator`: a `QueryValidator` to use by this server. Defaults to
`graphql.validate`.

`validation_rules`: a [`ValidationRules`](types-reference#validationrules) list or callable returning a
list of extra validation rules server should use to validate the
GraphQL queries. Defaults to `None`.

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

`execute_get_queries`: a `bool` that controls if `query` operations
sent using the `GET` method should be executed. Defaults to `False`.

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

`execution_context_class`: custom `ExecutionContext` type to use by
this server to execute the GraphQL queries. Defaults to standard
context type implemented by the `graphql`.


### Methods

#### `__call__`

```python
def __call__(self, environ: dict, start_response: Callable) -> List[bytes]:
    ...
```

An entrypoint to the WSGI application.

Returns list of bytes with response body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a callable used to begin new HTTP response.

Details about the arguments and their usage are described in PEP 3333:

https://peps.python.org/pep-3333/


#### `handle_graphql_error`

```python
def handle_graphql_error(
    self,
    error: GraphQLError,
    start_response: Callable,
) -> List[bytes]:
    ...
```

Handles a `GraphQLError` raised from `handle_request` and returns an
error response to the client.

Returns list of bytes with response body.


##### Required arguments

`error`: a `GraphQLError` instance.

`start_response`: a callable used to begin new HTTP response.


#### `handle_http_error`

```python
def handle_http_error(
    self,
    error: HttpError,
    start_response: Callable,
) -> List[bytes]:
    ...
```

Handles a `HttpError` raised from `handle_request` and returns an
error response to the client.

Returns list of bytes with response body.


##### Required arguments

`error`: a `HttpError` instance.

`start_response`: a callable used to begin new HTTP response.


#### `handle_request`

```python
def handle_request(
    self,
    environ: dict,
    start_response: Callable,
) -> List[bytes]:
    ...
```

Handles WSGI HTTP request and returns a a response to the client.

Returns list of bytes with response body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a callable used to begin new HTTP response.


#### `handle_get`

```python
def handle_get(self, environ: dict, start_response) -> List[bytes]:
    ...
```

Handles WSGI HTTP GET request and returns a response to the client.

Returns list of bytes with response body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a callable used to begin new HTTP response.


#### `handle_get_query`

```python
def handle_get_query(
    self,
    environ: dict,
    start_response,
    query_params: dict,
) -> List[bytes]:
    ...
```


#### `extract_data_from_get`

```python
def extract_data_from_get(self, query_params: dict) -> dict:
    ...
```

Extracts GraphQL data from GET request's querystring.

Returns a `dict` with GraphQL query data that was not yet validated.


##### Required arguments

`query_params`: a `dict` with parsed query string.


#### `handle_get_explorer`

```python
def handle_get_explorer(self, environ: dict, start_response) -> List[bytes]:
    ...
```

Handles WSGI HTTP GET explorer request and returns a response to the client.

Returns list of bytes with response body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a callable used to begin new HTTP response.


#### `handle_post`

```python
def handle_post(self, environ: dict, start_response: Callable) -> List[bytes]:
    ...
```

Handles WSGI HTTP POST request and returns a a response to the client.

Returns list of bytes with response body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a callable used to begin new HTTP response.


#### `get_request_data`

```python
def get_request_data(self, environ: dict) -> dict:
    ...
```

Extracts GraphQL request data from request.

Returns a `dict` with GraphQL query data that was not yet validated.


##### Required arguments

`environ`: a WSGI environment dictionary.


#### `extract_data_from_json_request`

```python
def extract_data_from_json_request(self, environ: dict) -> Any:
    ...
```

Extracts GraphQL data from JSON request.

Returns a `dict` with GraphQL query data that was not yet validated.


##### Required arguments

`environ`: a WSGI environment dictionary.


#### `get_request_content_length`

```python
def get_request_content_length(self, environ: dict) -> int:
    ...
```

Validates and returns value from `Content-length` header.

Returns an `int` with content length.

Raises a `HttpBadRequestError` error if `Content-length` header is
missing or invalid.


##### Required arguments

`environ`: a WSGI environment dictionary.


#### `get_request_body`

```python
def get_request_body(self, environ: dict, content_length: int) -> bytes:
    ...
```

Returns request's body.

Returns `bytes` with request body of specified length.

Raises a `HttpBadRequestError` error if request body is empty.


##### Required arguments

`environ`: a WSGI environment dictionary.

`content_length`: an `int` with content length.


#### `extract_data_from_multipart_request`

```python
def extract_data_from_multipart_request(self, environ: dict) -> Any:
    ...
```

Extracts GraphQL data from `multipart/form-data` request.

Returns an unvalidated `dict` with GraphQL query data.


##### Required arguments

`environ`: a WSGI environment dictionary.


#### `execute_query`

```python
def execute_query(self, environ: dict, data: dict) -> GraphQLResult:
    ...
```

Executes GraphQL query and returns its result.

Returns a [`GraphQLResult`](types-reference#graphqlresult), a two items long `tuple` with `bool` for
success and JSON-serializable `data` to return to client.


##### Required arguments

`environ`: a WSGI environment dictionary.

`data`: a GraphQL data.


#### `get_context_for_request`

```python
def get_context_for_request(
    self,
    environ: dict,
    data: dict,
) -> Optional[ContextValue]:
    ...
```

Returns GraphQL context value for HTTP request.

Default [`ContextValue`](types-reference#contextvalue) for WSGI application is a `dict` with single
`request` key that contains WSGI environment dictionary.


##### Required arguments

`environ`: a WSGI environment dictionary.

`data`: a GraphQL data.


#### `get_extensions_for_request`

```python
def get_extensions_for_request(
    self,
    environ: dict,
    context: Optional[ContextValue],
) -> ExtensionList:
    ...
```

Returns extensions to use when handling the GraphQL request.

Returns [`ExtensionList`](types-reference#extensionlist), a list of extensions to use or `None`.


##### Required arguments

`environ`: a WSGI environment dictionary.

`context`: a [`ContextValue`](types-reference#contextvalue) for this request.


#### `get_middleware_for_request`

```python
def get_middleware_for_request(
    self,
    environ: dict,
    context: Optional[ContextValue],
) -> Optional[MiddlewareList]:
    ...
```

Returns GraphQL middlewares to use when handling the GraphQL request.

Returns [`MiddlewareList`](types-reference#middlewarelist), a list of middlewares to use or `None`.


##### Required arguments

`environ`: a WSGI environment dictionary.

`context`: a [`ContextValue`](types-reference#contextvalue) for this request.


#### `return_response_from_result`

```python
def return_response_from_result(
    self,
    start_response: Callable,
    result: GraphQLResult,
) -> List[bytes]:
    ...
```

Returns WSGI response from GraphQL result.

Returns a list of bytes with response body.


##### Required arguments

`start_response`: a WSGI callable that initiates new response.

`result`: a [`GraphQLResult`](types-reference#graphqlresult) for this request.


#### `handle_not_allowed_method`

```python
def handle_not_allowed_method(
    self,
    environ: dict,
    start_response: Callable,
) -> List[bytes]:
    ...
```

Handles request for unsupported HTTP method.

Returns 200 response for `OPTIONS` request and 405 response for other
methods. All responses have empty body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a WSGI callable that initiates new response.


- - - - -


## `GraphQLMiddleware`

```python
class GraphQLMiddleware:
    ...
```

Simple WSGI middleware routing requests to either app or GraphQL.


### Constructor

```python
def __init__(
    self,
    app: Callable,
    graphql_app: Callable,
    path: str = '/graphql/',
):
    ...
```

Initializes the WSGI middleware.

Returns response from either application or GraphQL application


#### Required arguments

`app`: a WSGI application to route the request to if its path doesn't
match the `path` option.

`graphql_app`: a WSGI application to route the request to if its path
matches the `path` option.


#### Optional arguments

`path`: a `str` with a path to the GraphQL application. Defaults to
`/graphql/`.


### Methods

#### `__call__`

```python
def __call__(self, environ: dict, start_response: Callable) -> List[bytes]:
    ...
```

An entrypoint to the WSGI middleware.

Returns list of bytes with response body.


##### Required arguments

`environ`: a WSGI environment dictionary.

`start_response`: a callable used to start new HTTP response.


- - - - -


## `FormData`

```python
class FormData:
    ...
```

Feature-limited alternative of deprecated `cgi` standard package.

Holds the data from `multipart/form-data` request.


### Attributes

`charset`: a string with charset extracted from `Content-type` header.
Defaults to `latin-1`.

`fields`: an `dict` with form's fields names and values.

`files`: an `dict` with form's files names and values.


### Constructor

```python
def __init__(self, content_type: Optional[str]):
    ...
```

Initializes form data instance.


#### Optional arguments

`content_type`: a string with content type header's value. If not
provided, `latin-1` is used for content encoding.


### Methods

#### `parse_charset`

```python
def parse_charset(self, content_type: Optional[str]) -> Optional[str]:
    ...
```

Parses charset from `Content-type` header

Returns none if `content_type` is not provided, empty or missing the
`charset=` declaration.


##### Optional arguments

`content_type`: a string with content type header's value.


#### `on_field`

```python
def on_field(self, field) -> None:
    ...
```

Callback for HTTP request parser to provide field data.

Field name and value is decoded using the encoding stored in `encoding`
attribute and stored in `fields` attribute.


#### `on_file`

```python
def on_file(self, file) -> None:
    ...
```

Callback for HTTP request parser to provide file data.

File's field name is decoded using the encoding stored in `encoding`
attribute and stored in `files` attribute.


#### `getvalue`

```python
def getvalue(self, field_name: str) -> str:
    ...
```

Get form field's value.

Returns field's value or empty string if field didn't exist.


##### Required arguments

`field_name`: a `str` with name of form field to return the value for.