---
id: open-tracing
title: OpenTracing
---

> **Deprecation notice:** OpenTracing standard was superseded by [OpenTelemetry](./open-telemetry.md) and is considered deprecated. OpenTracing extension will be delete in a future version of Ariadne.

Ariadne provides an extension that implements the [OpenTracing](https://opentracing.io/) specification, making it easy to monitor GraphQL API performance and errors using popular APM tools like [Datadog](https://www.datadoghq.com/) or [Jaeger](https://www.jaegertracing.io/).

> **Note:** for performance reasons OpenTracing extension excludes default resolvers.


## Enabling OpenTracing in the API

To enable OpenTracing in your API, import the `OpenTracingExtension` class from `ariadne.contrib.tracing.opentracing` and pass it to your server `extensions` option:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.opentracing import OpenTracingExtension

app = GraphQL(
    schema,
    debug=True,
    http_handler=GraphQLHTTPHandler(
        extensions=[OpenTracingExtension],
    ),
)
```

> **Note:** If you don't have OpenTracing already configured in your project, you will need to install the [`opentracing-python`](https://github.com/opentracing/opentracing-python) package and [configure tracer](https://opentracing.io/guides/python/tracers/) for your APM solution.


## Configuration options

The `ariadne.contrib.tracing.opentracing` module exports `opentracing_extension` utility function that can be used to setup `OpenTracingExtension` with custom options:


### Filtering sensitive arguments data

By default all arguments field was resolved with are sent to the APM service. If your API fields have arguments for sensitive data like passwords or tokens, you will need to filter those before sending tracking data to the service.

`OpenTracingExtension` has configuration option named `arg_filter` which accepts a function that extension will call with the copy of the dict of arguments previously passed to field's resolver.

Here is an example defining custom filtering function named `my_arg_filter` and using `opentracing_extension` to setup OpenTracing with it:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing import opentracing_extension

def my_arg_filter(args, info):
    if "password" in args:
        args["password"] = "[redacted]"
    if "secret" in args:
        args["secret"] = "[redacted]"
    for key, value in args.items():
        if isinstance(value, dict):
            args[key] = my_arg_filter(value)
        if isinstance(value, list):
            args[key] = [my_arg_filter(v) for v in value]
    return args


schema = make_executable_schema(type_def, [query, mutation])
app = GraphQL(
    schema,
    debug=True,
    extensions=[
        opentracing_extension(arg_filter=my_arg_filter),
    ],
    http_handler=GraphQLHTTPHandler(
        extensions=[
            opentracing_extension(arg_filter=my_arg_filter),
        ],
    ),
)
```


### Customizing root span name

Ariadne uses `GraphQL Operation` for root span's name. You can customize this name using the `root_span_name` option:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing import opentracing_extension


schema = make_executable_schema(type_def, [query, mutation])
app = GraphQL(
    schema,
    debug=True,
    extensions=[
        opentracing_extension(arg_filter=my_arg_filter),
    ],
    http_handler=GraphQLHTTPHandler(
        extensions=[
            opentracing_extension(root_span_name="Admin GraphQL"),
        ],
    ),
)
```

You can also have a dynamic name by passing a function to the `root_span_name`:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing import opentracing_extension


def get_root_span_name(context) -> str:
    return context.get("operationName") or "GraphQL Mutation"


schema = make_executable_schema(type_def, [query, mutation])
app = GraphQL(
    schema,
    debug=True,
    extensions=[
        opentracing_extension(arg_filter=my_arg_filter),
    ],
    http_handler=GraphQLHTTPHandler(
        extensions=[
            opentracing_extension(root_span_name=get_root_span_name),
        ],
    ),
)
```
