"""Tests for subscription handler base class."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from starlette.testclient import TestClient

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.subscription_handlers.handlers import (
    SubscriptionHandler,
)


class MockSubscriptionHandler(SubscriptionHandler):
    """Mock handler for testing."""

    def __init__(self, should_support: bool = True):
        self.should_support = should_support
        self.handle_called = False
        self.handle_args = None

    def supports(self, request, data):
        return self.should_support

    async def handle(self, request, data, **kwargs):
        self.handle_called = True
        self.handle_args = {"request": request, "data": data, **kwargs}
        from starlette.responses import JSONResponse

        return JSONResponse({"handled": True})


def test_subscription_handler_requires_inheritance():
    """Test that objects must inherit from SubscriptionHandler."""

    class NotAHandler:
        def supports(self, request, data):
            return True

        async def handle(self, request, data, **kwargs):
            pass

    handler = NotAHandler()
    assert not isinstance(handler, SubscriptionHandler)


def test_mock_handler_supports():
    """Test MockSubscriptionHandler.supports()."""
    handler_true = MockSubscriptionHandler(should_support=True)
    handler_false = MockSubscriptionHandler(should_support=False)

    assert handler_true.supports(Mock(), {}) is True
    assert handler_false.supports(Mock(), {}) is False


@pytest.fixture
def simple_schema():
    type_defs = """
        type Query {
            hello: String!
        }
    """
    return make_executable_schema(type_defs)


def test_http_handler_with_subscription_handlers(simple_schema):
    """Test that GraphQLHTTPHandler accepts subscription_handlers."""
    handler = MockSubscriptionHandler()
    http_handler = GraphQLHTTPHandler(subscription_handlers=[handler])

    assert http_handler.subscription_handlers == [handler]


def test_http_handler_subscription_handlers_default_empty(simple_schema):
    """Test that GraphQLHTTPHandler has empty subscription_handlers by default."""
    http_handler = GraphQLHTTPHandler()

    assert http_handler.subscription_handlers == []


def test_http_handler_delegates_to_subscription_handler(simple_schema):
    """Test that GraphQLHTTPHandler delegates to subscription handler."""
    handler = MockSubscriptionHandler(should_support=True)
    app = GraphQL(
        simple_schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )

    client = TestClient(app)
    response = client.post("/", json={"query": "{ hello }"})

    assert handler.handle_called is True
    assert response.json() == {"handled": True}


def test_http_handler_skips_unsupported_handler(simple_schema):
    """Test that GraphQLHTTPHandler skips handlers that don't support request."""
    handler1 = MockSubscriptionHandler(should_support=False)
    handler2 = MockSubscriptionHandler(should_support=True)
    app = GraphQL(
        simple_schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler1, handler2]),
    )

    client = TestClient(app)
    response = client.post("/", json={"query": "{ hello }"})

    assert handler1.handle_called is False
    assert handler2.handle_called is True
    assert response.json() == {"handled": True}


def test_http_handler_falls_back_to_normal_handling(simple_schema):
    """Test that GraphQLHTTPHandler falls back when no handler supports request."""
    handler = MockSubscriptionHandler(should_support=False)
    app = GraphQL(
        simple_schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )

    client = TestClient(app)
    response = client.post("/", json={"query": "{ __typename }"})

    assert handler.handle_called is False
    # Falls back to normal query handling
    assert response.json() == {"data": {"__typename": "Query"}}


def test_http_handler_passes_schema_context_and_kwargs_to_handler(simple_schema):
    """Test that GraphQLHTTPHandler passes schema, context_value, and handler kwargs."""
    handler = MockSubscriptionHandler(should_support=True)
    app = GraphQL(
        simple_schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )

    client = TestClient(app)
    client.post("/", json={"query": "{ hello }"})

    assert handler.handle_called is True
    assert handler.handle_args is not None
    assert handler.handle_args["schema"] is simple_schema
    assert "context_value" in handler.handle_args
    assert handler.handle_args["root_value"] is None
    assert "query_parser" in handler.handle_args
    assert "query_validator" in handler.handle_args
    assert "validation_rules" in handler.handle_args
    assert "debug" in handler.handle_args
    assert "introspection" in handler.handle_args
    assert "logger" in handler.handle_args
    assert "error_formatter" in handler.handle_args


class GenerateEventsCollectorHandler(SubscriptionHandler):
    """Handler that uses generate_events and returns collected event types as JSON."""

    def supports(self, request, data):
        return isinstance(data, dict) and "subscription" in (data.get("query") or "")

    async def handle(self, request, data, **kwargs):
        from starlette.responses import JSONResponse

        events = []
        async for event in self.generate_events(data, query_document=None, **kwargs):
            events.append(
                {
                    "event_type": event.event_type.value,
                    "has_result": event.result is not None,
                    "has_errors": (
                        event.result.errors is not None and len(event.result.errors) > 0
                    )
                    if event.result
                    else False,
                }
            )
        return JSONResponse({"events": events})


@pytest.mark.asyncio
async def test_generate_events_yields_next_then_complete(schema):
    """
    Test that generate_events yields next events and then complete for a subscription.
    """
    handler = GenerateEventsCollectorHandler()
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )
    client = TestClient(app)

    response = client.post(
        "/",
        json={"query": "subscription { ping }"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "events" in body
    events = body["events"]
    assert len(events) >= 2
    assert events[0]["event_type"] == "next"
    assert events[0]["has_result"] is True
    assert events[0]["has_errors"] is False
    assert events[-1]["event_type"] == "complete"


@pytest.mark.asyncio
async def test_generate_events_yields_error_then_complete_on_invalid_query(schema):
    """
    Test that generate_events yields error event then complete for invalid subscription.
    """
    handler = GenerateEventsCollectorHandler()
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )
    client = TestClient(app)

    response = client.post(
        "/",
        json={"query": "subscription { nonexistent }"},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    body = response.json()
    events = body["events"]
    assert len(events) >= 2
    assert events[0]["event_type"] == "error"
    assert events[0]["has_errors"] is True
    assert events[-1]["event_type"] == "complete"


@pytest.mark.asyncio
async def test_generate_events_yields_error_then_complete_on_invalid_data(schema):
    """
    Test that generate_events yields error event then complete when data is invalid.
    """
    handler = GenerateEventsCollectorHandler()
    events = []
    async for event in handler.generate_events(
        {},
        schema=schema,
        context_value={},
        root_value=None,
        query_parser=None,
        query_validator=None,
        query_document=None,
        validation_rules=None,
        debug=False,
        introspection=True,
        logger=None,
        error_formatter=lambda e: {"message": str(e)},
    ):
        events.append(
            {
                "event_type": event.event_type.value,
                "has_errors": (
                    event.result.errors is not None and len(event.result.errors) > 0
                )
                if event.result
                else False,
            }
        )

    assert len(events) == 2
    assert events[0]["event_type"] == "error"
    assert events[0]["has_errors"] is True
    assert events[1]["event_type"] == "complete"


@pytest.mark.asyncio
async def test_generate_events_yields_error_on_source_exception(schema):
    """Test generate_events yields error when subscription source raises."""
    handler = GenerateEventsCollectorHandler()
    events = []
    async for event in handler.generate_events(
        {"query": "subscription { sourceError }"},
        schema=schema,
        context_value={},
        root_value=None,
        query_parser=None,
        query_validator=None,
        query_document=None,
        validation_rules=None,
        debug=False,
        introspection=True,
        logger=None,
        error_formatter=lambda e, debug: {"message": str(e)},
    ):
        error_message = None
        if event.result and event.result.errors:
            error_message = str(event.result.errors[0])
        events.append(
            {
                "event_type": event.event_type.value,
                "has_errors": (
                    event.result.errors is not None and len(event.result.errors) > 0
                )
                if event.result
                else False,
                "error_message": error_message,
            }
        )

    assert len(events) == 2
    assert events[0]["event_type"] == "error"
    assert events[0]["has_errors"] is True
    assert "Test exception" in events[0]["error_message"]
    assert events[1]["event_type"] == "complete"


@pytest.mark.asyncio
async def test_generate_events_handles_single_dict_error_response(schema):
    """
    Test that generate_events handles subscribe returning a single dict error.

    The subscribe function normally returns a list of errors when it fails.
    This test covers the defensive code path where results is not a list.
    """
    handler = GenerateEventsCollectorHandler()
    events = []

    # Mock subscribe to return a single dict error instead of a list
    mock_subscribe = AsyncMock(return_value=(False, {"message": "Single error"}))

    with patch("ariadne.subscription_handlers.handlers.subscribe", mock_subscribe):
        async for event in handler.generate_events(
            {"query": "subscription { ping }"},
            schema=schema,
            context_value={},
            root_value=None,
            query_parser=None,
            query_validator=None,
            query_document=None,
            validation_rules=None,
            debug=False,
            introspection=True,
            logger=None,
            error_formatter=lambda e, debug: {"message": str(e)},
        ):
            events.append(
                {
                    "event_type": event.event_type.value,
                    "has_errors": (
                        event.result.errors is not None and len(event.result.errors) > 0
                    )
                    if event.result
                    else False,
                    "error_message": (
                        str(event.result.errors[0])
                        if event.result and event.result.errors
                        else None
                    ),
                }
            )

    assert len(events) == 2
    assert events[0]["event_type"] == "error"
    assert events[0]["has_errors"] is True
    assert "Single error" in events[0]["error_message"]
    assert events[1]["event_type"] == "complete"
