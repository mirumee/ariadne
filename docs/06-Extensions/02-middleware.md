---
id: middleware
title: Middleware
---

GraphQL middleware are Python functions and callable objects that can be used to inject custom logic into query executor.

Middlewares share most of their arguments with [`resolvers`](../API-reference/types-reference#resolver), but take one extra argument: `resolver` callable that is resolver associated with currently resolved field:

```python
def lowercase_middleware(resolver, obj, info, **args)
```

> **Note**
>
> GraphQL middleware is sometimes confused with the ASGI or WSGI middleware, but its not the same thing!

> **Note**
>
> Middleware is not supported by subscriptions.


## Custom middleware example

Code below implements custom middleware that converts any strings returned by resolvers to lower case:

```python
from inspect import iscoroutinefunction

from graphql.pyutils import is_awaitable


def lowercase_middleware(resolver, obj, info, **args):
    if iscoroutinefunction(resolver):
        return lowercase_middleware_async(resolver, obj, info, **args)

    value = resolver(obj, info, **args)
    if is_awaitable(value):
        return lowercase_awaitable(value)

    return lowercase_value(await value)


async def lowercase_middleware_async(resolver, obj, info, **args):
    value = await resolver(obj, info, **args)
    if is_awaitable(value):
        return await lowercase_awaitable(value)

    return lowercase_value(await value)


async def lowercase_awaitable(value):
    return lowercase_value(await value)


def lowercase_value(value):
    if isinstance(value, str):
        return value.lower()

    return value
```

> **Note:** Please see the [asynchronous middleware](#asynchronous-middleware) section for an explanation for this implementation.

To use `lowercase_middleware` middleware in your queries, pass it to the `middleware` option of the HTTP handler:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler


def lowercase_middleware(resolver, obj, info, **args):
    value = resolver(obj, info, **args)
    if isinstance(value, str):
        return value.lower()
    return value


app = GrapqhQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        middleware=[lowercase_middleware],
    ),
)
```

In case when more than one middleware is enabled on the server, the `resolver` argument will point to the partial function constructed from the next middleware in the execution chain.


## Middleware managers

Middleware are ran through special class implemented by GraphQL named `MiddlewareManager`. If you want to replace this manager with custom one, you provide your own implementation using the `middleware_manager_class` option:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from graphql import GraphQLFieldResolver, MiddlewareManager


def lowercase_middleware(resolver, obj, info, **args):
    value = resolver(obj, info, **args)
    if isinstance(value, str):
        return value.lower()
    return value


class CustomMiddlewareManager(MiddlewareManager):
    def get_field_resolver(
        self, field_resolver: GraphQLFieldResolver
    ) -> GraphQLFieldResolver:
        """Wrap the provided resolver with the middleware.
        Returns a function that chains the middleware functions with the provided
        resolver function.
        """
        if self._middleware_resolvers is None:
            return field_resolver
        if field_resolver not in self._cached_resolvers:
            self._cached_resolvers[field_resolver] = reduce(
                lambda chained_fns, next_fn: partial(next_fn, chained_fns),
                self._middleware_resolvers,
                field_resolver,
            )
        return self._cached_resolvers[field_resolver]


app = GrapqhQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        middleware=[lowercase_middleware],
        middleware_manager_class=CustomMiddlewareManager,
    ),
)
```


## Middleware and extensions

Extensions [`resolve`](../API-reference/types-reference#resolve) hook is actually a middleware. In case when GraphQL server is configured to use both middleware and extensions, extensions `resolve` hooks will be executed before the `middleware` functions.


## Performance impact

Middlewares are called for **EVERY** resolver call.

Considering this query:

```graphql
{
    users {
        id
        email
        username
    }
}
```

If `users` resolver returns 100 users, middleware function will be called 301 times:

- one time for `Query.users` resolver
- 100 times for `id`
- 100 times for `email`
- 100 times for username

Avoid implementing costful or slow logic in middlewares. Use python decorators applied explicitly to resolver functions or ASGI/WSGI middlewares combined with callable `context_value`.


### Asynchronous middleware

In the [custom middleware example](#custom-middleware-example) above single synchronous middleware was implemented that supported following cases:

- Asynchronous resolver returning a value.
- Asynchronous resolver returning awaitable a value.
- Synchronous resolver returning a value.
- Synchronous resolver returning awaitable a value.

Converting this middleware to async would greatly simplify the implementation:

```python
from graphql.pyutils import is_awaitable


async def lowercase_middleware(resolver, obj, info, **args):
    if iscoroutinefunction(resolver):
        value = await resolver(obj, info, **args)
    else:
        value = resolver(obj, info, **args)

    if is_awaitable(value):
        value = await value

    if isinstance(value, str):
        return value.lower()

    return value
```

However, asynchronous middleware require for their result being `awaited` during query execution. Asynchronous functions in Python are considered fast, but the overhead of being sent to the event loop and having their result retrieved makes them **much** slower than plain synchronous function call for scenarios where no IO is involved. Because default implementation of middleware manager calls middlewares for every field in result set, this effectively turns all resolver calls in query executor into asynchronous calls. This makes query execution noticeably slower even for small GraphQL queries, and quick benchmarks have found that it can slow queries by x1.5 to x2.5.