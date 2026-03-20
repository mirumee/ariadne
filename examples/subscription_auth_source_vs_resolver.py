"""
Example: Bearer auth in a source, logging middleware in resolver, delivered over SSE.

This example demonstrates how to:
- Guard a subscription source with Bearer token authentication
- Apply resolver-level middleware (logging) to subscription resolvers

Run with:
    uvicorn examples.subscription_auth_source_vs_resolver:app --reload
or:
    uv run --with "uvicorn[standard]" --with ariadne \
        uvicorn examples.subscription_auth_source_vs_resolver:app --reload

Then test with curl:

    # With Bearer token — streams counter values via SSE
    curl -N -X POST http://localhost:8000/graphql/ \
      -H "Content-Type: application/json" \
      -H "Accept: text/event-stream" \
      -H "Authorization: Bearer mytoken" \
      -d '{"query": "subscription { counter }"}'

    # Without Bearer token — source raises PermissionError immediately
    curl -N -X POST http://localhost:8000/graphql/ \
        -H "Content-Type: application/json" \
        -H "Accept: text/event-stream" \
        -d '{"query": "subscription { counter }"}'
"""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any

from graphql import GraphQLResolveInfo
from starlette.applications import Starlette

from ariadne import QueryType, SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sse import SSESubscriptionHandler

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bearer auth helpers
# ---------------------------------------------------------------------------


def get_bearer_token(info: GraphQLResolveInfo) -> str | None:
    ctx = getattr(info, "context", None) or {}
    req = ctx.get("request") if isinstance(ctx, dict) else None
    if not req or not hasattr(req, "headers"):
        return None
    a = req.headers.get("Authorization", "")
    return a[7:].strip() if a.startswith("Bearer ") else None


def require_bearer_token_source(fn):
    """Decorator for subscription sources that require a Bearer token."""

    @wraps(fn)
    async def wrapper(obj: Any, info: GraphQLResolveInfo, **kw: Any):
        if not get_bearer_token(info):
            raise PermissionError("Missing Authorization: Bearer <token>")
        async for v in fn(obj, info, **kw):
            yield v

    return wrapper


def log_resolver(fn):
    @wraps(fn)
    def wrapper(obj: Any, info: GraphQLResolveInfo, **kw: Any) -> Any:
        result = fn(obj, info, **kw)
        log.info("resolver %s obj=%r", info.field_name, obj)
        return result

    return wrapper


type_defs = """
    type Query {
        ping: String
    }

    type Subscription {
        counter: Int
    }
"""

query = QueryType()
subscription = SubscriptionType()


@query.field("ping")
def resolve_ping(*_: Any) -> str:
    return "pong"


@subscription.source("counter")
@require_bearer_token_source
async def counter_source(*_: Any):
    for i in range(5):
        await asyncio.sleep(0.5)
        yield i


@subscription.field("counter")
@log_resolver
def resolve_counter(obj: Any, info: GraphQLResolveInfo) -> Any:
    return obj


schema = make_executable_schema(type_defs, query, subscription)

graphql_app = GraphQL(
    schema,
    debug=True,
    http_handler=GraphQLHTTPHandler(
        subscription_handlers=[SSESubscriptionHandler()],
    ),
)

app = Starlette()
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
