---
id: exceptions-reference
title: Exceptions reference
sidebar_label: ariadne.exceptions
---

Ariadne defines some custom exception types that can be imported from `ariadne.exceptions` module:



## `GraphQLFileSyntaxError`

```python
class GraphQLFileSyntaxError(Exception):
    ...
```

Raised by `load_schema_from_path` when loaded GraphQL file has invalid syntax.


### Constructor

```python
def __init__(self, file_path: Union[str, os.PathLike], message: str):
    ...
```

Initializes the `GraphQLFileSyntaxError` with file name and error.


#### Required arguments

`file_path`: a `str` or `PathLike` object pointing to a file that
failed to validate.

`message`: a `str` with validation message.


### Methods

#### `format_message`

```python
def format_message(
    self,
    file_path: Union[str, os.PathLike],
    message: str,
) -> None:
    ...
```

Builds final error message from path to schema file and error message.

Returns `str` with final error message.


##### Required arguments

`file_path`: a `str` or `PathLike` object pointing to a file that
failed to validate.

`message`: a `str` with validation message.


#### `__str__`

```python
def __str__(self) -> None:
    ...
```

Returns error message.


- - - - -


## `HttpBadRequestError`

```python
class HttpBadRequestError(HttpError):
    ...
```

Raised when request did not contain the data required to execute
the GraphQL query.


### Constructor

```python
def __init__(self, message: Optional[str] = None):
    ...
```

Initializes the `HttpBadRequestError` with optional error message.


- - - - -


## `HttpError`

```python
class HttpError(Exception):
    ...
```

Base class for HTTP errors raised inside the ASGI and WSGI servers.


### Constructor

```python
def __init__(self, status: str, message: Optional[str] = None):
    ...
```

Initializes the `HttpError` with a status and optional error message.


#### Arguments

`status`: HTTP status code as `HttpStatusResponse`.
`message`: Optional error message to return in the response body.


- - - - -


## `HttpStatusResponse`

```python
class HttpStatusResponse(Enum):
    ...
```


- - - - -


## `WebSocketConnectionError`

```python
class WebSocketConnectionError(Exception):
    ...
```

Special error class enabling custom error reporting for on_connect


### Constructor

```python
def __init__(self, payload: Optional[Union[dict, str]] = None):
    ...
```