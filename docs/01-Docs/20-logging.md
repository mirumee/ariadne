---
id: logging
title: Logging
---


Ariadne logs all errors using the default `ariadne` logger. To define a custom logger instead, pass its name to the `logger` argument when instantiating your application:

```python
from ariadne.wsgi import GraphQL
from .schema import schema

app = GraphQL(schema, logger="admin.graphql")
```

The `logger` argument is supported by the following functions and objects:

- `ariadne.graphql`
- `ariadne.graphql_sync`
- `ariadne.subscribe`
- `ariadne.asgi.GraphQL`
- `ariadne.wsgi.GraphQL`

Example with a custom logger (ASGI):

```python
from ariadne.asgi import GraphQL
from .schema import schema

app = GraphQL(schema, logger="myapp.graphql")
```

**See also:** [Mutations](mutations) and [Error messaging](error-messaging) for patterns that benefit from consistent logging when debugging failures.
