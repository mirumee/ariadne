"""Subscription handlers package for pluggable HTTP-based subscription protocols.

This package provides a Strategy Pattern implementation for handling GraphQL
subscriptions over HTTP-based transport protocols like SSE and HTTP callbacks.
These handlers are used with `GraphQLHTTPHandler` via its `subscription_handlers`
parameter. WebSocket-based subscriptions are handled separately by dedicated
handlers (`GraphQLWSHandler` and `GraphQLTransportWSHandler`).
"""

from .events import SubscriptionEvent, SubscriptionEventType
from .handlers import SubscriptionHandler

__all__ = [
    "SubscriptionEvent",
    "SubscriptionEventType",
    "SubscriptionHandler",
]
