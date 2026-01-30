---
id: apollo-tracing
title: Apollo Tracing
---

> **Deprecation notice:** Apollo Tracing has been deprecated and will be removed in a future version of Ariadne.

[Apollo Tracing](https://blog.apollographql.com/exposing-trace-data-for-your-graphql-server-with-apollo-tracing-97c5dd391385) exposes basic performance data of GraphQL queries: Query execution time and execution time of individual resolvers. Ariadne has GraphQL extension that includes this data in the JSON returned by the server after completing the query.

> **Note:** for performance reasons Apollo Tracing extension excludes default resolvers.


## Enabling Apollo Tracing in the API

To enable Apollo Tracing in your API, import the `ApolloTracingExtension` class from `ariadne.contrib.tracing.apollotracing` and pass it to your server `extensions` option:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension

app = GraphQL(
    schema,
    debug=True,
    http_handler=GraphQLHTTPHandler(
        extensions=[ApolloTracingExtension],
    ),
)
```


## Tracing default resolvers

For performance reasons tracing is disabled for default resolvers. To reverse this behavior you can initialize `ApolloTracingExtension` with `trace_default_resolver` option set to `True`:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension


def apollo_tracing():
    return ApolloTracingExtension(trace_default_resolver=True)


app = GraphQL(
    schema,
    debug=True,
    http_handler=GraphQLHTTPHandler(
        extensions=[apollo_tracing],
    ),
)
```