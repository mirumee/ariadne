"""Tests for SSESubscriptionHandler.

These tests mirror the tests in tests/asgi/test_sse.py but use the new
SSESubscriptionHandler with GraphQLHTTPHandler instead of the deprecated
GraphQLHTTPSSEHandler.
"""

import json
from http import HTTPStatus
from typing import Any
from unittest.mock import Mock

import pytest
from graphql import GraphQLError, parse
from httpx import Response
from starlette.testclient import TestClient

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sse import SSESubscriptionHandler

SSE_HEADER = {"Accept": "text/event-stream"}


def get_sse_events(response: Response) -> list[dict[str, Any]]:
    """Parse SSE response into a list of events."""
    events = []
    for event in response.text.split("\r\n\r\n"):
        if len(event.strip()) == 0:
            continue
        if "\r\n" not in event:
            # ping message
            events.append({"event": "", "data": None})
        else:
            event, data = event.split("\r\n", 1)
            event = event.replace("event: ", "")
            data = data.replace("data: ", "")
            data = json.loads(data) if len(data) > 0 else None
            events.append({"event": event, "data": data})
    return events


@pytest.fixture
def sse_client(schema):
    """Test client with SSESubscriptionHandler configured."""
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[
                SSESubscriptionHandler(
                    default_response_headers={"Test_Header": "test"}
                ),
            ]
        ),
        introspection=False,
    )
    return TestClient(app, headers=SSE_HEADER)


def test_sse_headers(sse_client):
    """Test that SSE response has correct headers."""
    response = sse_client.post("/", json={"query": "subscription { ping }"})
    assert response.status_code == HTTPStatus.OK
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["Connection"] == "keep-alive"
    assert response.headers["Transfer-Encoding"] == "chunked"
    assert response.headers["X-Accel-Buffering"] == "no"


def test_field_can_be_subscribed_to_using_sse(sse_client):
    """Test that subscriptions work via SSE."""
    response = sse_client.post("/", json={"query": "subscription { ping }"})
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"]["data"] == {"ping": "pong"}
    assert events[1]["event"] == "complete"


def test_non_subscription_query_cannot_be_executed_using_sse(sse_client):
    """Test that non-subscription queries return error via SSE."""
    response = sse_client.post(
        "/",
        json={
            "query": "query Hello($name: String){ hello(name: $name) }",
            "variables": {"name": "John"},
        },
    )
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"].get("errors") is not None


def test_invalid_query_is_handled_using_sse(sse_client):
    """Test that invalid queries return error via SSE."""
    response = sse_client.post("/", json={"query": "query Invalid { error other }"})
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"].get("errors") is not None


def test_custom_query_parser_is_used_for_subscription_over_sse(schema):
    """Test that custom query parser is used for SSE subscriptions."""
    mock_parser = Mock(return_value=parse("subscription { testContext }"))
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[SSESubscriptionHandler()]
        ),
        query_parser=mock_parser,
        context_value={"test": "I'm context"},
        root_value={"test": "I'm root"},
    )

    client = TestClient(app, headers=SSE_HEADER)
    response = client.post("/", json={"query": "subscription { testRoot }"})

    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"]["data"] == {"testContext": "I'm context"}
    assert events[1]["event"] == "complete"


@pytest.mark.parametrize(
    ("errors"),
    [
        ([]),
        ([GraphQLError("Nope")]),
    ],
)
def test_custom_query_validator_is_used_for_subscription_over_sse(schema, errors):
    """Test that custom query validator is used for SSE subscriptions."""
    mock_validator = Mock(return_value=errors)
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[SSESubscriptionHandler()]
        ),
        query_validator=mock_validator,
        context_value={"test": "I'm context"},
        root_value={"test": "I'm root"},
    )

    client = TestClient(app, headers=SSE_HEADER)
    response = client.post(
        "/",
        json={
            "operationName": None,
            "query": "subscription { testContext }",
            "variables": None,
        },
    )

    events = get_sse_events(response)
    if not errors:
        assert len(events) == 2
        assert events[0] == {
            "event": "next",
            "data": {"data": {"testContext": "I'm context"}},
        }
        assert events[1] == {"event": "complete", "data": None}
    else:
        assert len(events) == 2
        assert events[0]["data"]["errors"][0]["message"] == "Nope"


def test_schema_not_set_graphql_sse():
    """Test that an exception is raised when schema is not set.

    Note: In the new architecture with SSESubscriptionHandler, when schema is None,
    the subscription handler is NOT invoked (because GraphQLHTTPHandler checks
    `self.schema` before delegating to subscription handlers). Instead, the request
    falls through to execute_graphql_query which raises TypeError.

    This is different from the deprecated GraphQLHTTPSSEHandler which caught this
    error and returned it as an SSE event. The new behavior treats a missing schema
    as a server misconfiguration that should fail early.
    """
    app = GraphQL(
        None,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[SSESubscriptionHandler()]
        ),
    )

    client = TestClient(app, headers=SSE_HEADER)
    with pytest.raises(TypeError, match="schema is not set"):
        client.post(
            "/",
            json={
                "operationName": None,
                "query": "subscription { testContext }",
                "variables": None,
            },
        )


def test_ping_is_sent_sse(sse_client):
    """Test that ping/keepalive events are sent for slow subscriptions."""
    response = sse_client.post("/", json={"query": "subscription { testSlow }"})
    events = get_sse_events(response)
    assert len(events) == 4
    assert events[0]["event"] == "next"
    assert events[0]["data"]["data"] == {"testSlow": "slow"}
    assert events[1]["event"] == ""  # ping
    assert events[1]["data"] is None
    assert events[2]["event"] == "next"
    assert events[2]["data"]["data"] == {"testSlow": "slow"}
    assert events[3]["event"] == "complete"


def test_custom_ping_interval(schema):
    """Test that custom ping interval is respected."""
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[SSESubscriptionHandler(ping_interval=8)]
        ),
        introspection=False,
    )
    sse_client = TestClient(app, headers=SSE_HEADER)
    response = sse_client.post("/", json={"query": "subscription { testSlow }"})
    events = get_sse_events(response)
    assert len(events) == 5
    assert events[0]["event"] == "next"
    assert events[0]["data"]["data"] == {"testSlow": "slow"}
    assert events[1]["event"] == ""  # ping
    assert events[1]["data"] is None
    assert events[2]["event"] == ""  # second ping
    assert events[2]["data"] is None
    assert events[3]["event"] == "next"
    assert events[3]["data"]["data"] == {"testSlow": "slow"}
    assert events[4]["event"] == "complete"


def test_resolver_error_is_handled_sse(sse_client):
    """Test that resolver errors are handled correctly via SSE."""
    response = sse_client.post("/", json={"query": "subscription { resolverError }"})
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"]["errors"][0]["message"] == "Test exception"
    assert events[1]["event"] == "complete"


def test_default_headers_are_applied(sse_client):
    """Test that custom default headers are applied to SSE response."""
    response = sse_client.post("/", json={"query": "subscription { ping }"})
    assert response.headers["Test_Header"] == "test"


def test_sse_handler_supports_returns_true_for_sse_request(schema):
    """Test that SSESubscriptionHandler.supports() returns True for SSE requests."""
    handler = SSESubscriptionHandler()
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.headers = {"Accept": "text/event-stream"}

    assert handler.supports(mock_request, {"query": "subscription { ping }"}) is True


def test_sse_handler_supports_returns_false_for_get_request():
    """Test that SSESubscriptionHandler.supports() returns False for GET requests."""
    handler = SSESubscriptionHandler()
    mock_request = Mock()
    mock_request.method = "GET"
    mock_request.headers = {"Accept": "text/event-stream"}

    assert handler.supports(mock_request, {}) is False


def test_sse_handler_supports_returns_false_without_accept_header():
    """
    Test that SSESubscriptionHandler.supports() returns False without SSE Accept header.
    """
    handler = SSESubscriptionHandler()
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.headers = {"Accept": "application/json"}

    assert handler.supports(mock_request, {}) is False


def test_sse_handler_supports_returns_true_with_multiple_accept_values():
    """Test that SSESubscriptionHandler.supports() works with multiple Accept values."""
    handler = SSESubscriptionHandler()
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.headers = {"Accept": "application/json, text/event-stream"}

    assert handler.supports(mock_request, {}) is True


def test_falls_back_to_normal_query_without_sse_header(schema):
    """Test that non-SSE requests fall back to normal HTTP handling."""
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(
            subscription_handlers=[SSESubscriptionHandler()]
        ),
    )
    client = TestClient(app)

    response = client.post(
        "/",
        json={"query": '{ hello(name: "World") }'},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.json() == {"data": {"hello": "Hello, World!"}}
