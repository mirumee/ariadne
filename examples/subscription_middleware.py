"""
Example: Middleware in subscriptions (SSE).

This example demonstrates using GraphQL middleware with subscriptions
delivered via Server-Sent Events (SSE). Middleware functions intercept
resolver calls and can modify inputs or outputs, which is useful for
logging, authorization, data transformation, etc.

Run with:

    uvicorn examples.subscription_middleware:app --reload

or:
    uv run --with "uvicorn[standard]" --with ariadne \
        uvicorn examples.subscription_middleware:app --reload

Test with curl:

    curl -N -H "Content-Type: application/json" \
         -H "Accept: text/event-stream" \
         -d '{"query":"subscription { counter(to: 3) { value timestamp } }"}' \
         http://localhost:8000/graphql/
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from graphql import GraphQLResolveInfo
from starlette.applications import Starlette

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sse import SSESubscriptionHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

type_defs = """
    type Query {
        _unused: Boolean
    }

    type Subscription {
        counter(from: Int = 0, to: Int = 5, delay: Float = 0.5): CounterPayload!
    }

    type CounterPayload {
        value: Int!
        timestamp: String!
    }
"""

subscription = SubscriptionType()


@subscription.source("counter")
async def counter_source(obj: Any, info: GraphQLResolveInfo, **kwargs: Any):
    """Async generator emitting integers."""
    start = int(kwargs.get("from", 0))
    stop = int(kwargs.get("to", 5))
    delay = float(kwargs.get("delay", 0.5))

    current = start
    while current < stop:
        yield {"value": current, "timestamp": datetime.now().isoformat()}
        await asyncio.sleep(delay)
        current += 1


@subscription.field("counter")
def resolve_counter(payload, *args, **kwargs):
    """Resolver passes through the payload dict."""
    return payload


def logging_middleware(resolver, obj, info: GraphQLResolveInfo, **args):
    """Middleware that logs every resolver call."""
    field_name = info.field_name
    parent_type = info.parent_type.name
    logger.info("Resolving %s.%s", parent_type, field_name)
    return resolver(obj, info, **args)


schema = make_executable_schema(type_defs, subscription)

graphql_app = GraphQL(
    schema,
    debug=True,
    http_handler=GraphQLHTTPHandler(
        subscription_handlers=[SSESubscriptionHandler()],
        middleware=[logging_middleware],
    ),
)

app = Starlette()
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
