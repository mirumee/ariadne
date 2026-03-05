"""
Example: Subscriptions with the legacy graphql-ws protocol.

This example configures Ariadne's ASGI app with `GraphQLWSHandler`, which
implements the older `graphql-ws` subprotocol used by the
`subscriptions-transport-ws` client.

Run with:

    uvicorn examples.graphql_ws_subscription_example:app --reload
or:
    uv run --with "uvicorn[standard]" --with ariadne \\
        uvicorn examples.graphql_ws_subscription_example:app --reload
"""

import asyncio
from typing import Any

from starlette.applications import Starlette

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLWSHandler
from ariadne.explorer.playground import ExplorerPlayground

type_defs = """
    type Query {
        _unused: Boolean
    }

    type Subscription {
        ticker(limit: Int! = 1.0): Int!
    }
"""

subscription = SubscriptionType()


@subscription.source("ticker")
async def ticker_source(*_, **kwargs: dict[str, Any]):
    """
    Async generator emitting a counter number every second until limit is reached.
    """
    limit = kwargs.get("limit")
    for _counter in range(limit):
        yield _counter
        await asyncio.sleep(1)


@subscription.field("ticker")
def resolve_ticker(value, *args, **kwargs):
    return value


schema = make_executable_schema(type_defs, subscription)

graphql_app = GraphQL(
    schema,
    debug=True,
    websocket_handler=GraphQLWSHandler(),
    explorer=ExplorerPlayground(title="Ariadne graphql-ws example"),
)

app = Starlette()
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
