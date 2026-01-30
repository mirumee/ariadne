---
id: open-telemetry
title: OpenTelemetry
---

Ariadne provides an extension that implements the [OpenTelemetry](https://opentelemetry.io/) specification, enabling monitoring of GraphQL API performance and errors using popular APM tools like [Datadog](https://www.datadoghq.com/) or [Jaeger](https://www.jaegertracing.io/).

> **Note:** for performance reasons OpenTelemetry extension excludes default resolvers.


## Enabling OpenTelemetry in the API

To enable OpenTelemetry in your API, import the `OpenTelemetryExtension` class from `ariadne.contrib.tracing.opentelemetry` and pass it to your server `extensions` option:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.opentelemetry import OpenTelemetryExtension

app = GraphQL(
    schema,
    debug=True,
    http_handler=GraphQLHTTPHandler(
        extensions=[OpenTelemetryExtension],
    ),
)
```

> **Note:** If you don't have OpenTelemetry already configured in your project, you will need to install the [`opentelemetry-api`](https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-api) package and [configure tracer](https://opentelemetry.io/docs/specs/otel/trace/sdk/) for your APM solution.


## Configuration options

The `ariadne.contrib.tracing.opentelemetry` module exports `opentelemetry_extension` utility function that can be used to setup `OpenTelemetryExtension` with custom options:


### Filtering sensitive arguments data

By default all arguments field was resolved with are sent to the APM service. If your API fields have arguments for sensitive data like passwords or tokens, you will need to filter those before sending tracking data to the service.

`OpenTelemetryExtension` has configuration option named `arg_filter` which accepts a function that extension will call with the copy of the dict of arguments previously passed to field's resolver.

Here is an example defining custom filtering function named `my_arg_filter` and using `opentelemetry_extension` to setup OpenTelemetry with it:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing import opentelemetry_extension

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
        opentelemetry_extension(arg_filter=my_arg_filter),
    ],
    http_handler=GraphQLHTTPHandler(
        extensions=[
            opentelemetry_extension(arg_filter=my_arg_filter),
        ],
    ),
)
```


### Customizing root span name

Ariadne uses `GraphQL Operation` for root span's name. You can customize this name using the `root_span_name` option:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing import opentelemetry_extension


schema = make_executable_schema(type_def, [query, mutation])
app = GraphQL(
    schema,
    debug=True,
    extensions=[
        opentelemetry_extension(arg_filter=my_arg_filter),
    ],
    http_handler=GraphQLHTTPHandler(
        extensions=[
            opentelemetry_extension(root_span_name="Admin GraphQL"),
        ],
    ),
)
```

You can also have a dynamic name by passing a function to the `root_span_name`:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing import opentelemetry_extension


def get_root_span_name(context) -> str:
    return context.get("operationName") or "GraphQL Mutation"


schema = make_executable_schema(type_def, [query, mutation])
app = GraphQL(
    schema,
    debug=True,
    extensions=[
        opentelemetry_extension(arg_filter=my_arg_filter),
    ],
    http_handler=GraphQLHTTPHandler(
        extensions=[
            opentelemetry_extension(root_span_name=get_root_span_name),
        ],
    ),
)
```