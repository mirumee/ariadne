"""
Example: HTTP Callback Subscription Handler

This example demonstrates how to implement a custom subscription handler that
delivers subscription events via HTTP callbacks instead of persistent connections.

This pattern is useful for gateway architectures where:
- Client connects to gateway via SSE
- Gateway forwards subscription requests to DGS (Domain Graph Service)
- DGS executes subscriptions and posts callbacks to gateway
- Gateway delivers events to a client

Workflow:
1. Client -> Gateway: SSE connection at /subscriptions/sse
2. Gateway -> DGS: HTTP POST to /subscriptions/gateway with callbackUri
3. DGS -> Gateway: Returns 204 immediately, starts a background task
4. DGS -> Gateway: Posts KEEP_ALIVE, DATA, COMPLETE, or CLOSE messages
5. Gateway -> DGS: Responds with status (ACCEPTED, SUCCESS, CONNECTION_CLOSED, etc.)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from logging import Logger, LoggerAdapter
from typing import Any

import httpx
from graphql import GraphQLSchema
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.format_error import format_error
from ariadne.subscription_handlers import SubscriptionHandler
from ariadne.subscription_handlers.events import (
    SubscriptionEvent,
    SubscriptionEventType,
)
from ariadne.types import (
    ErrorFormatter,
    QueryParser,
    QueryValidator,
    RootValue,
    ValidationRules,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("callback_handler")

# -----------------------------------------------------------------------------
# Message Types and Data Classes (matching gateway protocol)
# -----------------------------------------------------------------------------


class MessageType(str, Enum):
    """Types of callback messages sent to the gateway."""

    KEEP_ALIVE = "KEEP_ALIVE"  # Heartbeat to keep connection alive
    DATA = "DATA"  # Subscription data payload
    COMPLETE = "COMPLETE"  # Normal completion, no more data
    CLOSE = "CLOSE"  # Error/early termination


class ResultStatus(str, Enum):
    """Status codes returned by the gateway."""

    ACCEPTED = "ACCEPTED"  # Message accepted, delivery pending
    SUCCESS = "SUCCESS"  # Message delivered to a client
    IO_EXCEPTION = "IO_EXCEPTION"  # I/O error during delivery
    CONNECTION_CLOSED = "CONNECTION_CLOSED"  # Client disconnected
    NOT_FOUND = "NOT_FOUND"  # Subscription ID unknown


@dataclass
class SubscriptionMessage:
    """Message payload sent to the callback endpoint."""

    subscription_id: str
    type: MessageType
    data: dict[str, Any] | None = None
    errors: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict for HTTP POST."""
        result: dict[str, Any] = {
            "subscriptionId": self.subscription_id,
            "type": self.type.value,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.errors is not None:
            result["errors"] = self.errors
        return result


@dataclass
class CallbackResponse:
    """Response received from the callback endpoint."""

    status: ResultStatus
    raw_response: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CallbackResponse":
        """Parse from callback endpoint response JSON."""
        status_str = data.get("status", "ACCEPTED")
        try:
            status = ResultStatus(status_str)
        except ValueError:
            status = ResultStatus.ACCEPTED
        return cls(status=status, raw_response=data)

    def should_terminate(self) -> bool:
        """Check if this response indicates the subscription should stop."""
        return self.status in (
            ResultStatus.IO_EXCEPTION,
            ResultStatus.CONNECTION_CLOSED,
            ResultStatus.NOT_FOUND,
        )


@dataclass
class CallbackMetadata:
    """Metadata extracted from the subscription request."""

    subscription_id: str
    callback_uri: str
    callback_app_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# HTTP Callback Subscription Handler
# -----------------------------------------------------------------------------


class CallbackSubscriptionHandler(SubscriptionHandler):
    """Subscription handler that delivers events via HTTP callbacks.

    This handler is designed for gateway architectures where the GraphQL server
    (DGS) sends subscription events to a gateway via HTTP POST requests.

    The handler:
    1. Extracts callback metadata from the request extensions
    2. Returns 204 No Content immediately with a BackgroundTask
    3. Executes the subscription in the background task
    4. Posts events (DATA, KEEP_ALIVE, COMPLETE, CLOSE) to the callback URI
    5. Terminates if the gateway responds with an error status

    # Example usage

    ```python
    from ariadne.asgi import GraphQL
    from ariadne.asgi.handlers import GraphQLHTTPHandler

    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[CallbackSubscriptionHandler()]),
    )
    ```

    # Request format

    The subscription request should include callback metadata in extensions:

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
    """

    def __init__(
        self,
        keep_alive_interval: float = 5.0,
        callback_timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the callback subscription handler.

        # Optional arguments

        `keep_alive_interval`: seconds between KEEP_ALIVE messages (default: 5.0)

        `callback_timeout`: HTTP timeout for callback requests (default: 10.0)

        `max_retries`: number of retry attempts for failed callbacks (default: 3)

        `retry_delay`: seconds to wait between retries (default: 1.0)
        """
        self.keep_alive_interval = keep_alive_interval
        self.callback_timeout = callback_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def supports(self, request: Request, data: dict) -> bool:
        """Check if this handler supports the given request.

        Returns True if the request contains callback metadata in extensions.
        """
        return self._extract_metadata(data) is not None

    def _extract_metadata(self, data: dict) -> CallbackMetadata | None:
        """Extract callback metadata from request data.

        Expected format in extensions:
        {
            "subscription": {
                "callbackUri": "...",
                "subscriptionId": "...",
                "callbackAppId": "..."  # optional
            }
        }
        """
        extensions = data.get("extensions")
        if not isinstance(extensions, dict):
            return None

        subscription = extensions.get("subscription")
        if not isinstance(subscription, dict):
            return None

        callback_uri = subscription.get("callbackUri")
        subscription_id = subscription.get("subscriptionId")

        if not callback_uri or not subscription_id:
            return None

        return CallbackMetadata(
            subscription_id=subscription_id,
            callback_uri=callback_uri,
            callback_app_id=subscription.get("callbackAppId"),
            extra={
                k: v
                for k, v in subscription.items()
                if k not in ("callbackUri", "subscriptionId", "callbackAppId")
            },
        )

    async def handle(
        self,
        request: Request,
        data: dict,
        *,
        schema: GraphQLSchema,
        context_value: Any,
        root_value: RootValue | None,
        query_parser: QueryParser | None,
        query_validator: QueryValidator | None,
        validation_rules: ValidationRules | None,
        debug: bool,
        introspection: bool,
        logger: None | str | Logger | LoggerAdapter,
        error_formatter: ErrorFormatter,
    ) -> Response:
        """Handle the subscription request via HTTP callbacks.

        Returns 204 immediately and executes subscription in a Starlette BackgroundTask.
        """
        metadata = self._extract_metadata(data)

        # Return 204 with background task for subscription execution
        return Response(
            status_code=204,
            background=BackgroundTask(
                self._execute_subscription,
                data=data,
                metadata=metadata,
                schema=schema,
                context_value=context_value,
                root_value=root_value,
                query_parser=query_parser,
                query_validator=query_validator,
                validation_rules=validation_rules,
                debug=debug,
                introspection=introspection,
                logger=logger,
                error_formatter=error_formatter,
            ),
        )

    async def _execute_subscription(
        self,
        data: dict,
        metadata: CallbackMetadata,
        **kwargs,
    ) -> None:
        """Execute the subscription and deliver events via callbacks."""
        terminated = False
        keep_alive_task: asyncio.Task | None = None

        logger.info(
            "[sub:%s] Starting subscription execution (callback_uri=%s)",
            metadata.subscription_id,
            metadata.callback_uri,
        )

        async with httpx.AsyncClient(timeout=self.callback_timeout) as client:
            try:
                # Start keep-alive task
                logger.info(
                    "[sub:%s] Starting keep-alive task (interval=%.1fs)",
                    metadata.subscription_id,
                    self.keep_alive_interval,
                )
                keep_alive_task = asyncio.create_task(
                    self._send_periodic_keep_alive(client, metadata)
                )

                # Process subscription events
                async for event in self.generate_events(
                    data,
                    query_document=None,
                    **kwargs,
                ):
                    response = await self._send_event(client, metadata, event)

                    if response and response.should_terminate():
                        logger.warning(
                            "[sub:%s] Gateway responded with %s, terminating",
                            metadata.subscription_id,
                            response.status.value,
                        )
                        terminated = True
                        break

            except Exception as e:
                logger.error(
                    "[sub:%s] Subscription error: %s",
                    metadata.subscription_id,
                    e,
                )
                # Send CLOSE message on error
                if not terminated:
                    await self._send_callback(
                        client,
                        metadata,
                        SubscriptionMessage(
                            subscription_id=metadata.subscription_id,
                            type=MessageType.CLOSE,
                            errors=[{"message": str(e)}],
                        ),
                    )

            finally:
                # Cancel keep-alive task
                if keep_alive_task:
                    logger.info(
                        "[sub:%s] Cancelling keep-alive task",
                        metadata.subscription_id,
                    )
                    keep_alive_task.cancel()
                    try:
                        await keep_alive_task
                    except asyncio.CancelledError:
                        pass

                logger.info(
                    "[sub:%s] Subscription execution finished",
                    metadata.subscription_id,
                )

    async def _send_event(
        self,
        client: httpx.AsyncClient,
        metadata: CallbackMetadata,
        event: SubscriptionEvent,
    ) -> CallbackResponse | None:
        """Convert a SubscriptionEvent to a callback message and send it."""
        message = self._event_to_message(metadata.subscription_id, event)
        logger.info(
            "[sub:%s] Sending event: type=%s data=%s errors=%s",
            metadata.subscription_id,
            message.type.value,
            message.data,
            message.errors,
        )
        return await self._send_callback(client, metadata, message)

    def _event_to_message(
        self,
        subscription_id: str,
        event: SubscriptionEvent,
    ) -> SubscriptionMessage:
        """Convert a SubscriptionEvent to a SubscriptionMessage."""
        if event.event_type == SubscriptionEventType.COMPLETE:
            return SubscriptionMessage(
                subscription_id=subscription_id,
                type=MessageType.COMPLETE,
            )

        if event.event_type == SubscriptionEventType.KEEP_ALIVE:
            return SubscriptionMessage(
                subscription_id=subscription_id,
                type=MessageType.KEEP_ALIVE,
            )

        # NEXT or ERROR events
        data = None
        errors = None

        if event.result is not None:
            if event.result.data is not None:
                data = event.result.data
            if event.result.errors:
                errors = [format_error(e) for e in event.result.errors]

        # Use CLOSE for errors, DATA for data
        if errors and not data:
            return SubscriptionMessage(
                subscription_id=subscription_id,
                type=MessageType.CLOSE,
                errors=errors,
            )

        return SubscriptionMessage(
            subscription_id=subscription_id,
            type=MessageType.DATA,
            data=data,
            errors=errors,
        )

    async def _send_periodic_keep_alive(
        self,
        client: httpx.AsyncClient,
        metadata: CallbackMetadata,
    ) -> None:
        """Send KEEP_ALIVE callbacks at regular intervals."""
        keep_alive_count = 0
        while True:
            await asyncio.sleep(self.keep_alive_interval)
            keep_alive_count += 1
            logger.debug(
                "[sub:%s] Sending KEEP_ALIVE #%d",
                metadata.subscription_id,
                keep_alive_count,
            )
            response = await self._send_callback(
                client,
                metadata,
                SubscriptionMessage(
                    subscription_id=metadata.subscription_id,
                    type=MessageType.KEEP_ALIVE,
                ),
            )

            if response and response.should_terminate():
                logger.warning(
                    "[sub:%s] Keep-alive got termination response: %s",
                    metadata.subscription_id,
                    response.status.value,
                )
                break

    async def _send_callback(
        self,
        client: httpx.AsyncClient,
        metadata: CallbackMetadata,
        message: SubscriptionMessage,
    ) -> CallbackResponse | None:
        """Send a callback message with retry logic."""
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "[sub:%s] POST %s [%s] (attempt %d/%d)",
                    metadata.subscription_id,
                    metadata.callback_uri,
                    message.type.value,
                    attempt + 1,
                    self.max_retries,
                )
                response = await client.post(
                    metadata.callback_uri,
                    json=message.to_dict(),
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

                try:
                    callback_response = CallbackResponse.from_dict(response.json())
                except Exception:
                    # If response isn't valid JSON, assume success
                    callback_response = CallbackResponse(status=ResultStatus.SUCCESS)

                logger.debug(
                    "[sub:%s] Callback response: status=%s (HTTP %d)",
                    metadata.subscription_id,
                    callback_response.status.value,
                    response.status_code,
                )
                return callback_response

            except Exception as e:
                logger.warning(
                    "[sub:%s] Callback failed (attempt %d/%d): %s",
                    metadata.subscription_id,
                    attempt + 1,
                    self.max_retries,
                    e,
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)

        logger.error(
            "[sub:%s] All %d callback attempts failed for %s message",
            metadata.subscription_id,
            self.max_retries,
            message.type.value,
        )
        return None


# -----------------------------------------------------------------------------
# Example GraphQL Schema
# -----------------------------------------------------------------------------

type_defs = """
    type Query {
        _empty: String
    }

    type Subscription {
        counter(limit: Int = 5): Int!
    }
"""

subscription = SubscriptionType()


@subscription.source("counter")
async def counter_generator(*_, limit: int = 5):
    """Simple counter that emits integers."""
    for i in range(limit):
        yield i
        await asyncio.sleep(1)


@subscription.field("counter")
def resolve_counter(count, *_, **kwargs):
    return count


schema = make_executable_schema(type_defs, subscription)


# -----------------------------------------------------------------------------
# Application Setup
# -----------------------------------------------------------------------------


def create_app() -> Starlette:
    """Create the Starlette application with callback subscription support."""

    # GraphQL app with callback handler
    graphql_app = GraphQL(
        schema,
        debug=True,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[CallbackSubscriptionHandler()]
        ),
    )

    # Mock gateway callback endpoint (for testing)
    async def mock_callback(request: Request) -> Response:
        """Mock callback endpoint that simulates gateway responses."""
        body = await request.json()
        msg_type = body.get("type", "UNKNOWN")
        sub_id = body.get("subscriptionId", "?")
        logger.info(
            "[gateway] Received %s from subscription %s | data=%s errors=%s",
            msg_type,
            sub_id,
            body.get("data"),
            body.get("errors"),
        )

        # Simulate gateway response
        return JSONResponse({"status": "SUCCESS"})

    # Create app with routes
    app = Starlette(
        debug=True,
        routes=[
            Route("/callback", mock_callback, methods=["POST"]),
        ],
    )
    app.mount("/graphql", graphql_app)

    return app


app = create_app()


# -----------------------------------------------------------------------------
# Example Client Usage
# -----------------------------------------------------------------------------

"""
To test the callback subscription handler:

1. Install required dependencies:

   pip install ariadne starlette uvicorn httpx

2. Start the server (from the ariadne root directory):

   uvicorn examples.subscription_handler_example:app --reload

   Or run directly with Python:

   python examples/subscription_handler_example.py
   
   Or run with uv:
   uv run \
      --with uvicorn \
      --with ariadne \
      --with starlette \
      --with httpx \
      uvicorn examples.subscription_handler_example:app --reload


3. Send a subscription request with callback metadata:

   curl -X POST http://localhost:8000/graphql/ \
     -H "Content-Type: application/json" \
     -d '{
       "query": "subscription { counter(limit: 3) }",
       "extensions": {
         "subscription": {
           "callbackUri": "http://localhost:8000/callback",
           "subscriptionId": "test-123",
           "callbackAppId": "my-app"
         }
       }
     }'

4. You should receive a 204 No Content response immediately.

5. Watch the server logs to see callback messages being sent:
   - KEEP_ALIVE messages every 5 seconds
   - DATA messages with counter values
   - COMPLETE message when the subscription ends
"""


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
