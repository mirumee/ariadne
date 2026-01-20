"""
Example: Synchronous Generator Subscriptions

This example demonstrates how to use synchronous generators as subscription sources
in Ariadne GraphQL. Synchronous generators are automatically executed in worker threads
to avoid blocking the event loop.
"""

import time

from starlette.applications import Starlette

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL

# Create subscription type
subscription = SubscriptionType()


# Example 1: Simple synchronous generator with blocking sleep
@subscription.source("timeUpdates")
def time_updates(*_, interval: int = 1):
    """Emit current time at specified intervals using blocking sleep."""
    count = 0
    while count < 10:  # Limit to 10 updates for demo
        yield {
            "timestamp": time.time(),
            "count": count,
        }
        time.sleep(interval)  # Blocking sleep - OK in sync generators!
        count += 1


@subscription.field("timeUpdates")
def resolve_time_updates(message, *_):
    """Resolver for time updates."""
    return message


# Example 2: Synchronous generator with database-like simulation
@subscription.source("dataStream")
def data_stream(*_, limit: int = 5):
    """Simulate streaming data from a synchronous source."""
    for i in range(limit):
        # Simulate blocking I/O operation
        time.sleep(0.5)
        yield {
            "id": i + 1,
            "value": f"data_{i + 1}",
            "processed": True,
        }


@subscription.field("dataStream")
def resolve_data_stream(message, *_):
    """Resolver for data stream."""
    return message


# Example 3: Mixed sync and async generators
@subscription.source("asyncData")
async def async_data(*_):
    """Example async generator for comparison."""
    import asyncio

    for i in range(3):
        yield {"type": "async", "value": i}
        await asyncio.sleep(0.1)


@subscription.field("asyncData")
def resolve_async_data(message, *_):
    """Resolver for async data."""
    return message


# Define GraphQL schema
type_defs = """
    type Query {
        _: Boolean
    }
    
    type Subscription {
        timeUpdates(interval: Int): TimeUpdate!
        dataStream(limit: Int): DataItem!
        asyncData: AsyncData!
    }
    
    type TimeUpdate {
        timestamp: Float!
        count: Int!
    }
    
    type DataItem {
        id: ID!
        value: String!
        processed: Boolean!
    }
    
    type AsyncData {
        type: String!
        value: Int!
    }
"""

# Create executable schema
schema = make_executable_schema(type_defs, subscription)

# Create ASGI app
app = Starlette()
graphql_app = GraphQL(schema, debug=True)
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
