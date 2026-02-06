"""Subscription event abstraction for HTTP-based subscription handlers."""

from dataclasses import dataclass
from enum import Enum

from graphql import ExecutionResult


class SubscriptionEventType(Enum):
    """Type of subscription event."""

    NEXT = "next"
    ERROR = "error"
    COMPLETE = "complete"
    KEEP_ALIVE = "keep_alive"


@dataclass
class SubscriptionEvent:
    """Represents a subscription event for HTTP-based subscription handlers.

    This is a representation of subscription events used by `SubscriptionHandler`
    subclasses to deliver subscription data over HTTP-based protocols
    (SSE, HTTP callbacks, etc.). These events are used with `GraphQLHTTPHandler`
    and are not related to WebSocket-based subscription handlers.

    # Attributes

    `event_type`: the type of the event (next, error, complete, keep_alive)

    `result`: an optional `ExecutionResult` containing the subscription data or errors
    """

    event_type: SubscriptionEventType
    result: ExecutionResult | None = None
