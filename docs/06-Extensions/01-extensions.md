---
id: extensions
title: Extension system
---

Ariadne implements simple extension system that allows developers to inject custom python logic into the query execution process. This system was designed with performance measurement extensions in mind but may potentially support other use cases.

> At the moment adding extensions to subscriptions is not supported.


## Enabling extensions

To enable extensions, initialize handler with `extensions` parameter. This parameter accepts list of [extensions](../API-reference/types-reference#extension):

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler

from .schema import schema
from .extensions import MyExtension


app = GraphQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        extensions=[MyExtension],
    ),
)
```

Alternatively, if your extension depends on request or should be enabled conditionally, you can provide callable that will return extensions that should be used:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler

from .schema import schema
from .extensions import MyExtension


def get_extensions(request, context):
    if request.headers.get("x-enable-my-extension"):
        return [MyExtension]
    return None


app = GraphQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        extensions=get_extensions,
    ),
)
```


## Custom extension example

Let's create simple extension that measures query execution time, and appends this time to query's result.

All extensions should extend special base class named [`Extension`](../API-reference/types-reference#extension), importable from `ariadne.types`:

```python
from ariadne.types import Extension


class QueryExecutionTimeExtension(Extension):
    ...
```

Our extension will measure the query execution time. This means we need to measure the time of two events, request start and creation of JSON response:

```python
import time

from ariadne.types import Extension


class QueryExecutionTimeExtension(Extension):
    def __init__(self):
        self.start_timestamp = None
        self.end_timestamp = None

    def request_started(self, context):
        self.start_timestamp = time.perf_counter_ns()

    def format(self, context):
        if self.start_timestamp and self.end_timestamp:
            return {
                "execution": time.perf_counter_ns() - self.start_timestamp
            }
```

> See [`Extension`](../API-reference/types-reference#extension) reference for the list of available events.
