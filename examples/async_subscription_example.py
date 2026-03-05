"""
Example: Async subscriptions with the graphql-transport-ws protocol.

This example uses an async generator as the subscription source and configures
the ASGI app with `GraphQLTransportWSHandler`, which implements the
`graphql-transport-ws` WebSocket subprotocol.

Run with:

    uvicorn examples.async_subscription_example:app --reload

or:
    uv run --with "uvicorn[standard]" --with ariadne \\
        uvicorn examples.async_subscription_example:app --reload
"""

import asyncio
from typing import Any

from graphql import GraphQLResolveInfo
from starlette.applications import Starlette

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler

type_defs = """
    type Query {
        _unused: Boolean
    }

    type Subscription {
        counter(from: Int = 0, to: Int = 5, delay: Float = 0.5): Int!
    }
"""

subscription = SubscriptionType()


@subscription.source("counter")
async def counter_source(obj: Any, info: GraphQLResolveInfo, **kwargs: Any):
    """Async generator emitting integers from `from` (inclusive) to `to`."""
    start = int(kwargs.get("from", 0))
    stop = int(kwargs.get("to", 5))
    delay = float(kwargs.get("delay", 0.5))

    current = start
    while current < stop:
        yield current
        await asyncio.sleep(delay)
        current += 1


@subscription.field("counter")
def resolve_counter(value, *args, **kwargs):
    """Resolver passes through values from the source."""
    return value


schema = make_executable_schema(type_defs, subscription)

graphql_app = GraphQL(
    schema,
    debug=True,
    websocket_handler=GraphQLTransportWSHandler(),
)

app = Starlette()
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
