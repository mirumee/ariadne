---
id: asgi
title: ASGI application
---

Ariadne provides a `GraphQL` class that implements a production-ready ASGI application.


## Using with an ASGI server

First create an application instance pointing it to the schema to serve:

```python
# in myasgi.py
import os

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from mygraphql import type_defs, resolvers

schema = make_executable_schema(type_defs, resolvers)
application = GraphQL(schema)
```

Then point an ASGI server such as uvicorn at the above instance.

Example using uvicorn:

```console
$ uvicorn myasgi:application
```


## Configuration options

See the [reference](asgi-reference.md#constructor).


## The `request` instance

The ASGI application creates its own `request` object, an instance of the `Request` class from the [Starlette](https://github.com/encode/starlette/blob/0.36.1/starlette/requests.py#L199). It's `scope` and `receive` attributes are populated from the received request.

When writing the [ASGI middleware](https://asgi.readthedocs.io/en/latest/specs/main.html#middleware), remember to rely on the `request.scope` dict for storing additional data on the request object, instead of mutating the request object directly (like it's done in Django). For example:

```python
# This is wrong
request.app_data

# This is correct
request.scope["app_data"]
```


## Customizing JSON responses

Ariadne's ASGI application uses [Starlette's `JSONResponse`](https://github.com/encode/starlette/blob/0.36.1/starlette/responses.py#L169) for its JSON responses.

You can customize response creation logic by implementing a custom HTTP handler strategy for your ASGI GraphQL app.

To star, create a custom class extending the `GraphQLHTTPHandler` from `ariadne.asgi.handlers` package:

```python
from ariadne.asgi.handlers import GraphQLHTTPHandler


class CustomGraphQLHTTPHandler(GraphQLHTTPHandler):
    pass
```

Next, implement a customized version of the [`create_json_response`](./asgi-handlers-reference.md#create_json_response) method:

```python
import json
from http import HTTPStatus

from ariadne.asgi.handlers import GraphQLHTTPHandler
from starlette.requests import Request
from starlette.responses import Response


class CustomGraphQLHTTPHandler(GraphQLHTTPHandler):
    async def create_json_response(
        self,
        request: Request,  # pylint: disable=unused-argument
        result: dict,
        success: bool,
    ) -> Response:
        status_code = HTTPStatus.OK if success else HTTPStatus.BAD_REQUEST
        content = json.dumps(
            result,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

        return Response(
            content,
            status_code=status_code,
            media_type="application/json"
        )
```

Finally, update the `GraphQL` instance used in your project to use the `CustomGraphQLHTTPHandler`:

```python
from ariadne.asgi import GraphQL

# Rest of code...

app = GraphQL(
    schema,
    http_handler=CustomGraphQLHTTPHandler(),
)
```

Your `GraphQL` will now use the `CustomGraphQLHTTPHandler` strategy that we've just implemented to create JSON responses.

> **Note**: the `GraphQLHTTPHandler` class implements many other methods that can be customized through inheritance.
>
> See the [API reference](./asgi-handlers-reference.md#graphqlhttphandler) for a completed list.
