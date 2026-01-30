---
id: subscriptions
title: Subscriptions
---


Let's introduce a third type of operation. While queries offer a way to query a server once, subscriptions offer a way for the server to notify the client each time new data is available.

This is where the `Subscription` type is useful. It's similar to `Query` but as each subscription remains an open channel you can send anywhere from zero to millions of responses over its lifetime.

> Because of their nature, subscriptions are only possible to implement in asynchronous servers that implement the WebSockets protocol.
> (If you are using `uvicorn` you need to `pip install websockets` otherwise you'll get `Could not connect to websocket endpoint ws://localhost:8000/. Please check if the endpoint url is correct.`)
>
> *WSGI*-based servers (including Django) are synchronous in nature and *unable* to handle WebSockets which makes them incapable of implementing subscriptions.
>
> If you wish to use subscriptions with Django, consider wrapping your Django application in a Django Channels container and using Ariadne as an *ASGI* server.


## Subscription protocols

In the world of GraphQL clients, there are two subscription protocols that clients can implement for subscribing to GraphQL server.


### `subscriptions-transport-ws`

Default protocol used by Ariadne. Client library for it is still widely used although no it's no longer maintained. It has benefit of being supported by GraphQL-Playground out of the box.

Repo link: [apollographql/subscriptions-transport-ws](https://github.com/apollographql/subscriptions-transport-ws)

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLWSHandler


graphql_app = GraphQL(
    schema,
    websocket_handler=GraphQLWSHandler(),
)
```


### `graphql-ws`

New protocol that replaced `subscriptions-transport-ws`. Its actively maintained and supported by Apollo Studio Explorer.

Repo link: [enisdenjo/graphql-ws](https://github.com/enisdenjo/graphql-ws)

To make Ariadne use `graphql-ws` protocol for subscriptions, initialize `ariadne.asgi.GraphQL` app with `ariadne.asgi.handlers.GraphQLTransportWSHandler` instance:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler


graphql_app = GraphQL(
    schema,
    websocket_handler=GraphQLTransportWSHandler(),
)
```

> **Note:** Name of class implementing `graphql-ws` is not a mistake. The subprotocol used for subscriptions is indeed named [`graphql-transport-ws`](https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md).


## Defining subscriptions

In schema definition subscriptions look similar to queries:

```graphql
type Query {
    _unused: Boolean
}

type Subscription {
    counter: Int!
}
```

This example contains:

- `Query` type with single unused field. GraphQL considers an empty type a syntax error and requires an API to always define a `Query` type.
    - For this example, we're focusing on `Subscription`s so we define a bare bones `Query` type.
- `Subscription` type with a single field, `counter`, that returns a number.

When defining subscriptions you can use all of the features of the schema such as arguments, input and output types.


## Writing subscriptions

Subscriptions are more complex than queries as they require us to provide two functions for each field:

- `generator` is a function that yields data we're going to send to the client. It has to implement the `AsyncGenerator` protocol.
- `resolver` that tells the server how to send data to the client. This is similar to the [resolvers we wrote earlier](resolvers).

> Make sure you understand how asynchronous generators work before attempting to use subscriptions.

The signatures are as follows:

```python
async def counter_generator(obj, info):
    for i in range(5):
        await asyncio.sleep(1)
        yield i


def counter_resolver(count, info):
    return count + 1
```

Note that the resolver consumes the same type (in this case `int`) that the generator yields.

Each time our source yields a response, it's getting sent to our resolver. The above implementation counts from zero to four, each time waiting for one second before yielding a value.

The resolver increases each number by one before passing them to the client so the client sees the counter progress from one to five.

After the last value is yielded the generator returns, the server tells the client that no more data will be available, and the subscription is complete.

We can map these functions to subscription fields using the `SubscriptionType` class that extends `ObjectType` with support for `source`:

```python
from ariadne import SubscriptionType
from . import counter_subscriptions

subscription = SubscriptionType()
subscription.set_field("counter", counter_subscriptions.counter_resolver)
subscription.set_source("counter", counter_subscriptions.counter_generator)
```

You can also use the `source` decorator:

```python
@subscription.source("counter")
async def counter_generator(
    obj: Any, info: GraphQLResolveInfo
) -> AsyncGenerator[int, None]:
    ...
```


## Publisher-consumer

Pubisher-consumer ("pub-sub") is a pattern in which parts of the system listen for ("subscribe to") events ("messages") from other parts of the system, usually reacting to them with very small delay.

To implement subscriptions, you will need to introduce a pub-sub solution to your stack. Multiple technologies are available here, starting with dedicated solutions like Apache Kafka, RabbitMQ and ending with data stores supporting subscribing to updates like Redis and PostgreSQL. Each of those solutions offers different features and trade offs, making them useful for different use-cases.

Only requirement by Ariadne is that technology has Python implementation that supports `async` subscriber.


### Simple pub-sub setup with Broadcaster

[Broadcaster](https://github.com/encode/broadcaster) is a simple pub-sub library that supports Redis, PostgreSQL and Apache Kafka as backends. It can be installed with `pip`:

```console
pip install broadcaster
```

In our example we will use Redis server running on localhost at port 6379 for messaging. We instantiate `Broadcaster` with connection URL in our app:

```python
broadcast = Broadcast("redis://localhost:6379")
```

We also need to run its `connect` and `disconnect` methods when our ASGI app starts or stops:

```python
app = Starlette(on_startup=[broadcast.connect], on_shutdown=[broadcast.disconnect])
```


### Publisher

We can publish our messages using the `publish` method:

```python
await broadcast.publish(channel="chatroom", message="Hello world!")
```

> **Note:** Channels are a way to group publishers and subscribers together. Your system may use single channel or multiple ones, each for different feature.

Where publishing code should live at? Simplest answer is _at the same place that events occur that you would like your users to subscribe to_. Here are few examples:

- In GraphQL mutations: `postComment` mutation could publish event to notify other clients on same page that new commend was posted.
- In task queues: `process_video_file` Celery task could publish event with current progress on processing uploaded video file.
- In regular views: your JSON API or standard HTTP form view can send an event that contact form was sent to notify customer service members on-line.


### Subscriber

Unlike publishers, which can go anywhere, subscribers in GraphQL API's have single dedicated place: subscriptions _source_:

```python
@subscription.source("chat")
async def chat_generator(
    _: Any, info: GraphQLResolveInfo
) -> AsyncGenerator[str, None]:
    async with broadcast.subscribe(channel="chatroom") as subscriber:
        async for message in subscriber:
            yield message
```

In addition to that, generators can be used to filter which messages should and which shouldn't be sent further to the subscribers:

```python
@subscription.source("chat")
async def chat_generator(
    _: Any, info: GraphQLResolveInfo
) -> AsyncGenerator[str, None]:
    swearwords = await load_swearwords()

    async with broadcast.subscribe(channel="chatroom") as subscriber:
        async for message in subscriber:
            if not contains_swearwords(message, swearwords):
                yield message
```


### Simple chat example:

Here's example implementing simple GraphQL chat with mutation for sending messages and subscription for receiving them:

```python
import json

from ariadne import MutationType, SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLWSHandler
from broadcaster import Broadcast
from starlette.applications import Starlette


broadcast = Broadcast("memory://")


type_defs = """
  type Query {
    _unused: Boolean
  }

  type Message {
    sender: String
    message: String
  }

  type Mutation {
    send(sender: String!, message: String!): Boolean
  }

  type Subscription {
    message: Message
  }
"""


mutation = MutationType()


@mutation.field("send")
async def resolve_send(*_, **message):
    await broadcast.publish(channel="chatroom", message=json.dumps(message))
    return True


subscription = SubscriptionType()


@subscription.source("message")
async def source_message(_, info):
    async with broadcast.subscribe(channel="chatroom") as subscriber:
        async for event in subscriber:
            yield json.loads(event.message)


schema = make_executable_schema(type_defs, mutation, subscription)
graphql = GraphQL(
    schema=schema,
    debug=True,
    websocket_handler=GraphQLWSHandler(),
)

app = Starlette(
    debug=True,
    on_startup=[broadcast.connect],
    on_shutdown=[broadcast.disconnect],
)

app.mount("/", graphql)
```

> **Note:** We have expanded the code above into a repository with complete example, including GraphQL server, React.js client, Redis for messaging and Uvicorn HTTP server.
>
> It can be found on our github: [Ariadne GraphQL Chat Example](https://github.com/mirumee/ariadne-graphql-chat-example)


## Connection params

Because subscriptions in GraphQL are done over the websockets, you can't use custom HTTP headers to pass additional data from client to server. This makes it impossible to use `Authorization` header for authentication within subscriptions.

To work around this limitation, websocket clients include this data in initial message sent to the server as part of connection negotiation.


### Using `on_connect` to access connection's parameters

To access connection parameters, custom function needs to be implemented and passed to Ariadne's `on_connect` option:

```python
from ariadne.asgi.handlers import GraphQLWSHandler


def on_connect(websocket, params: Any):
    ...


graphql = GraphQL(
    schema,
    websocket_handler=GraphQLWSHandler(
        on_connect=on_connect,
    ),
)
```

This function is called exactly once: at the time when websocket connection is opened by the client. It's always called with two arguments: a `starlette.websockets.WebSocket` instance and a payload. It can be synchronous or asynchronous.

Please note that because `params` value is set by the client there are no guarantees on what type and concents this value will be. Due care needs to be taken here:

```python
def on_connect(websocket, params: Any):
    if not isinstance(params, dict):
        return

    token = params.get("token")
    if token:
        ...
```

In order to make params available to the resolvers, they need to be passed through the `WebSocket.scope` dict to context factory:

```python
def on_connect(websocket, params: Any):
    if not isinstance(params, dict):
        websocket.scope["connection_params"] = {}
        return

    # websocket.scope is a dict acting as a "bag"
    # stores data for the duration of connection
    websocket.scope["connection_params"] = {
        "token": params.get("token"),
    }


def context_value(request_or_websocket, data):
    context = {}

    if request.scope["type"] == "websocket":
        # request is an instance of WebSocket
        context.update(request.scope["connection_params"])
    else:
        context["token"] = request.META.get("authorization")

    return context


graphql = GraphQL(
    schema,
    context_value=context_value,
    websocket_handler=GraphQLWSHandler(
        on_connect=on_connect,
    ),
)
```


### `on_connect` vs `context_value`

There's important difference between `on_connect` and `context_value`:

`on_connect` is called once, at the time of websocket connection negotiation between client and GraphQL server.

`context_value` is called every time new subscription query is made by the client.

If your client has two separate UI components (eg. notification bell on the navbar and list of on-line users), and those components do GraphQL `subscribe` queries, `context_value` will be ran for each of those separately while `on_connect` will only be ran once.

> **Note:** This behavior is true for most popular GraphQL client implementations (`gql` and Apollo-Client) but may not be true for some libraries.

This can have implications for application performance. It may be preferable to cache data on `websocket.scope` instead of `info.context` to avoid repeated database reads for multiple subscriptions accessing same data. Or pre-load user object in `on_connect`.


## Refusing websocket connection

To refuse websocket connection from client, you can raise `ariadne.asgi.WebSocketConnectionError` from `on_connect`:

```python
def on_connect(websocket, params: Any):
    if not isinstance(params, dict):
        raise WebSocketConnectionError("Invalid payload")

    token = params.get("token")
    if not token:
        raise WebSocketConnectionError("Missing auth")
```

If you have control on client implementation as well, you can pass custom error payload instead of string:

```python
def on_connect(websocket, params: Any):
    if not isinstance(params, dict):
        raise WebSocketConnectionError({"message": "Invalid payload", "code": "invalid_payload"})

    token = params.get("token")
    if not token:
        raise WebSocketConnectionError({"message": "Missing auth", "code": "auth"})
```


## `on_operation` and `on_complete`

> **Warning:** This feature is considered experimental. It was implemented for feature parity with older version of Apollo Server. Its final shape (or presence in future Ariadne releases) is snot decided yet. Generally you should try using `on_connect` and `on_disconnect` first before using those features.

`on_operation` and `on_complete` options allow you to run extra python code when client subscribes or unsubscribes from Subscription field within same WebSocket connection:

```python
def on_operation(websocket, operation: Operation):
    ...


def on_complete(websocket, operation: Operation):
    ...


graphql = GraphQL(schema, on_operation=on_operation, on_complete=on_complete)
```

First argument for those functions is `WebSocket` instance and second one is `Operation` dataclass storing data about current subscription:

```python
@dataclass
class Operation:
    id: str
    name: Optional[str]
    generator: AsyncGenerator
```


## `on_disconnect`

`on_disconnect` option can be set to callable function taking single argument, `WebSocket` instance, that should be ran after Ariadne closes the websocket connection:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLWSHandler


def on_connect(websocket, params: Any):
    if not isinstance(params, dict):
        websocket.scope["connection_params"] = {}
        return

    chat_user = get_user_from_ws(params)
    chat_user.set_online()
    websocket.scope["chat_user"] = chat_user


def on_disconnect(websocket):
    chat_user = websocket.scope.get("chat_user")
    if chat_user:
        chat_user.set_offline()


graphql = GraphQL(
    schema,
    websocket_handler=GraphQLWSHandler(
        on_connect=on_connect,
        on_disconnect=on_disconnect,
    ),
)
```


## Using Server-Sent Events Protocol

Instead of WebSockets, [Server-Sent Events (SSE)](https://github.com/enisdenjo/graphql-sse/blob/master/PROTOCOL.md) can be used as a transmission protocol for subscriptions. This approach uses single, long-lived HTTP connection to push data to clients.

To enable subscriptions over Server-Sent Events, initialize the `ariadne.asgi.GraphQL` app with an `ariadne.contrib.sse.GraphQLHTTPSSEHandler` instance:

```python
import asyncio
from typing import Any, AsyncGenerator

from ariadne import SubscriptionType, make_executable_schema, gql
from ariadne.asgi import GraphQL
from ariadne.contrib.sse import GraphQLHTTPSSEHandler

type_defs = gql("""

    type Query {
        _empty: String
    }

    type Subscription {
        counter: Int!
    }

""")

subscription = SubscriptionType()


@subscription.field("counter")
async def counter_resolver(count, info: Any) -> AsyncGenerator[int, None]:
    return count


@subscription.source("counter")
async def counter_generator(obj: Any, info: Any) -> AsyncGenerator[int, None]:
    for i in range(5):
        yield i
        await asyncio.sleep(1)


schema = make_executable_schema(type_defs, [subscription])
app = GraphQL(schema, http_handler=GraphQLHTTPSSEHandler())
```

Subscriptions can be consumed using the [graphql-sse](https://github.com/enisdenjo/graphql-sse/) JavaScript client library or any other compatible implementation.

> The `GraphQLHTTPSSEHandler` requires the ASGI server to work.
>
> This handler only supports the _distinct connections_ mode of the protocol due to Ariadne's stateless implementation.
>
> If you are using a custom client implementation, make sure to add the `Accept: text/event-stream` header to the request as this is required to establish the Server-Sent Events connection.