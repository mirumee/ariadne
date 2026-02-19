# Pluggable Subscription Handlers

Ariadne provides a pluggable subscription handler system for `GraphQLHTTPHandler` that allows implementing custom HTTP-based transport protocols for GraphQL subscriptions. This enables support for delivery mechanisms like Server-Sent Events (SSE), HTTP callbacks, and custom protocols.

> **Note:** WebSocket-based subscriptions are handled separately by dedicated handlers (`GraphQLWSHandler` and `GraphQLTransportWSHandler`). The pluggable subscription handler system described here is specifically for HTTP-based subscription transports configured via the `subscription_handlers` parameter of `GraphQLHTTPHandler`.

## Table of Contents

- [Overview](#overview)
- [Using Subscription Handlers](#using-subscription-handlers)
- [Creating Custom Handlers](#creating-custom-handlers)
- [Event System](#event-system)
- [HTTP Callback Handler Example](#http-callback-handler-example)
- [Combining Multiple Handlers](#combining-multiple-handlers)

## Overview

The subscription handler system uses the **Strategy Pattern** to decouple subscription execution from transport delivery. Each handler:

1. **Determines support**: Checks if it can handle a given request (via `supports()`)
2. **Handles the request**: Processes the subscription and delivers events (via `handle()`)
3. **Generates events**: Uses the shared `generate_events()` method to execute the subscription

```
HTTP Request → GraphQLHTTPHandler
                    ↓
              subscription_handlers[0].supports(request, data)?
                    ↓ Yes                    ↓ No
              handler.handle()         Try next handler...
                    ↓                        ↓ No handlers match
              generate_events()        Normal query/mutation execution
                    ↓
              SubscriptionEvent stream
                    ↓
              Transport-specific delivery (SSE, HTTP callback, etc.)
```

## Using Subscription Handlers

### Basic Setup

Pass subscription handlers to `GraphQLHTTPHandler`:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler

from myapp.handlers import MySubscriptionHandler

app = GraphQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        subscription_handlers=[
            MySubscriptionHandler(),
        ]
    ),
)
```

### Handler Selection

When a subscription request arrives, handlers are checked in order. The first handler whose `supports()` method returns `True` handles the request.

```python
http_handler=GraphQLHTTPHandler(
    subscription_handlers=[
        MyCustomHandler(),      # Checked first
        SSESubscriptionHandler(),  # Fallback
    ]
)
```

## Creating Custom Handlers

### The SubscriptionHandler Base Class

Custom handlers extend `SubscriptionHandler` and implement two methods:

```python
from ariadne.subscription_handlers import SubscriptionHandler
from starlette.requests import Request
from starlette.responses import Response


class MyCustomHandler(SubscriptionHandler):
    def supports(self, request: Request, data: dict) -> bool:
        """Return True if this handler should process the request."""
        # Check headers, extensions, or request data
        return "myCustomHeader" in request.headers

    async def handle(
        self,
        request: Request,
        data: dict,
        *,
        schema,
        context_value,
        root_value,
        query_parser,
        query_validator,
        validation_rules,
        debug,
        introspection,
        logger,
        error_formatter,
    ) -> Response:
        """Process the subscription and return a response."""
        # Use generate_events() to get subscription events
        async for event in self.generate_events(
            data,
            schema=schema,
            context_value=context_value,
            root_value=root_value,
            query_parser=query_parser,
            query_validator=query_validator,
            query_document=None,
            validation_rules=validation_rules,
            debug=debug,
            introspection=introspection,
            logger=logger,
            error_formatter=error_formatter,
        ):
            # Process each SubscriptionEvent
            # event.event_type: NEXT, ERROR, COMPLETE, KEEP_ALIVE
            # event.result: ExecutionResult (for NEXT/ERROR events)
            pass

        return Response(status_code=200)
```

### The generate_events() Method

The `generate_events()` method is provided by `SubscriptionHandler` and handles:

- Request validation
- GraphQL subscription execution
- Error handling and formatting
- Yielding `SubscriptionEvent` objects

You don't need to implement subscription execution logic—just consume the events and deliver them via your transport.

## Event System

### SubscriptionEventType

Events have one of four types:

```python
from ariadne.subscription_handlers.events import SubscriptionEventType

SubscriptionEventType.NEXT       # Contains subscription data
SubscriptionEventType.ERROR      # Contains error information
SubscriptionEventType.COMPLETE   # Subscription ended normally
SubscriptionEventType.KEEP_ALIVE # Connection maintenance
```

### SubscriptionEvent

```python
from ariadne.subscription_handlers.events import (
    SubscriptionEvent,
    SubscriptionEventType,
)
from graphql import ExecutionResult

# Create events using direct construction
event = SubscriptionEvent(
    event_type=SubscriptionEventType.NEXT,
    result=execution_result,
)
event = SubscriptionEvent(
    event_type=SubscriptionEventType.ERROR,
    result=execution_result,
)
event = SubscriptionEvent(event_type=SubscriptionEventType.COMPLETE)
event = SubscriptionEvent(event_type=SubscriptionEventType.KEEP_ALIVE)

# Access event data
event.event_type  # SubscriptionEventType
event.result      # ExecutionResult or None
```

### Processing Events

```python
async for event in self.generate_events(data, **kwargs):
    if event.event_type == SubscriptionEventType.NEXT:
        # event.result.data contains the subscription payload
        # event.result.errors may contain GraphQL errors
        pass

    elif event.event_type == SubscriptionEventType.ERROR:
        # Handle error - event.result.errors contains error details
        pass

    elif event.event_type == SubscriptionEventType.COMPLETE:
        # Subscription finished - clean up resources
        break

    elif event.event_type == SubscriptionEventType.KEEP_ALIVE:
        # Send keep-alive signal to client
        pass
```

## HTTP Callback Handler Example

This example shows how to implement a subscription handler for gateway architectures where events are delivered via HTTP callbacks instead of persistent connections.

### Use Case

```
Client ──SSE──> Gateway ──HTTP POST──> GraphQL Server (DGS)
                   ↑                          │
                   └────HTTP callbacks────────┘
```

1. Client connects to gateway via SSE
2. Gateway forwards subscription to DGS with a `callbackUri`
3. DGS returns 204 immediately
4. DGS posts events (DATA, KEEP_ALIVE, COMPLETE, CLOSE) to the callback URI
5. Gateway streams events to client

### Message Types

```python
from enum import Enum


class MessageType(str, Enum):
    KEEP_ALIVE = "KEEP_ALIVE"  # Heartbeat
    DATA = "DATA"              # Subscription data
    COMPLETE = "COMPLETE"      # Normal completion
    CLOSE = "CLOSE"            # Error/early termination


class ResultStatus(str, Enum):
    ACCEPTED = "ACCEPTED"           # Message accepted
    SUCCESS = "SUCCESS"             # Delivered to client
    IO_EXCEPTION = "IO_EXCEPTION"   # I/O error
    CONNECTION_CLOSED = "CONNECTION_CLOSED"  # Client disconnected
    NOT_FOUND = "NOT_FOUND"         # Unknown subscription ID
```

### Request Format

```json
{
    "query": "subscription { counter }",
    "extensions": {
        "subscription": {
            "callbackUri": "https://gateway.example.com/callback",
            "subscriptionId": "uuid-here",
            "callbackAppId": "my-app"
        }
    }
}
```

### Callback Payloads

**KEEP_ALIVE:**
```json
{
    "subscriptionId": "uuid-here",
    "type": "KEEP_ALIVE"
}
```

**DATA:**
```json
{
    "subscriptionId": "uuid-here",
    "type": "DATA",
    "data": {
        "counter": 42
    }
}
```

**COMPLETE:**
```json
{
    "subscriptionId": "uuid-here",
    "type": "COMPLETE"
}
```

**CLOSE (with error):**
```json
{
    "subscriptionId": "uuid-here",
    "type": "CLOSE",
    "errors": [{"message": "Subscription error: ..."}]
}
```

### Implementation

See `examples/subscription_handler_example.py` for a complete implementation that includes:

- Metadata extraction from request extensions
- Background task execution using Starlette's `BackgroundTask`
- Periodic keep-alive messages
- Retry logic for failed callbacks
- Early termination based on gateway response status

### Usage

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler

from myapp.handlers import CallbackSubscriptionHandler

app = GraphQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        subscription_handlers=[
            CallbackSubscriptionHandler(
                keep_alive_interval=5.0,
                callback_timeout=10.0,
                max_retries=3,
            )
        ]
    ),
)
```

## Combining Multiple Handlers

You can combine multiple handlers to support different clients:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sse import SSESubscriptionHandler

from myapp.handlers import CallbackSubscriptionHandler

app = GraphQL(
    schema,
    http_handler=GraphQLHTTPHandler(
        subscription_handlers=[
            # Gateway requests with callbackUri
            CallbackSubscriptionHandler(),
            # Browser clients with Accept: text/event-stream
            SSESubscriptionHandler(),
        ]
    ),
)
```

**Handler selection order matters**—the first matching handler processes the request.

### Selection Logic Examples

| Request                                       | Handler Selected              |
|-----------------------------------------------|-------------------------------|
| `extensions.subscription.callbackUri` present | `CallbackSubscriptionHandler` |
| `Accept: text/event-stream` header            | `SSESubscriptionHandler`      |
| Neither                                       | Falls through to HTTP handler |

## Best Practices

### 1. Resource Cleanup

Always clean up resources when the subscription ends:

```python
async def handle(self, request, data, **kwargs):
    try:
        async for event in self.generate_events(data, **kwargs):
            # Process events
            pass
    finally:
        # Cleanup: close connections, cancel tasks, etc.
        pass
```

### 2. Error Handling

Handle errors gracefully and send appropriate error events to clients:

```python
async def handle(self, request, data, **kwargs):
    try:
        async for event in self.generate_events(data, **kwargs):
            await self.deliver_event(event)
    except Exception as e:
        # Send error to client before closing
        await self.send_error(str(e))
        raise
```

### 3. Keep-Alive for Long Connections

For persistent connections, send periodic keep-alive signals:

```python
import asyncio


async def handle(self, request, data, **kwargs):
    keep_alive_task = asyncio.create_task(self.send_keep_alive())

    try:
        async for event in self.generate_events(data, **kwargs):
            await self.deliver_event(event)
    finally:
        keep_alive_task.cancel()
```

### 4. Background Tasks

For fire-and-forget delivery (like HTTP callbacks), use Starlette's `BackgroundTask`:

```python
from starlette.background import BackgroundTask
from starlette.responses import Response


async def handle(self, request, data, **kwargs):
    return Response(
        status_code=204,
        background=BackgroundTask(
            self._execute_subscription,
            data=data,
            **kwargs,
        ),
    )
```

### 5. Termination Handling

Respond to client disconnection or termination signals:

```python
async def _execute_subscription(self, data, **kwargs):
    terminated = False

    async for event in self.generate_events(data, **kwargs):
        response = await self.deliver_event(event)

        if self.should_terminate(response):
            terminated = True
            break

    if not terminated:
        await self.send_complete()
```

## Summary

The pluggable subscription handler system provides:

- **Flexibility**: Implement any transport protocol
- **Reusability**: Share subscription execution logic via `generate_events()`
- **Composability**: Combine multiple handlers for different clients
- **Clean separation**: Transport concerns separated from GraphQL execution

Ariadne is transport-agnostic—implement custom handlers for your specific needs: SSE for browser clients, HTTP callbacks for gateway architectures, or any other delivery mechanism. See `examples/subscription_handler_example.py` for a complete reference implementation.
