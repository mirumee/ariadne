import json
from http import HTTPStatus
from typing import List, Dict, Any
from unittest.mock import Mock
from graphql import parse, GraphQLError

from starlette.testclient import TestClient
from httpx import Response
import pytest
from ariadne.asgi import GraphQL

SSE_HEADER = {"Accept": "text/event-stream"}


def get_sse_events(response: Response) -> List[Dict[str, Any]]:
    events = []
    for event in response.text.split("\r\n\r\n"):
        if len(event.strip()) == 0:
            continue
        event, data = event.split("\r\n", 1)
        event = event.replace("event: ", "")
        data = data.replace("data: ", "")
        data = json.loads(data) if len(data) > 0 else None
        events.append({"event": event, "data": data})
    return events


@pytest.fixture
def sse_client(schema):
    app = GraphQL(schema, introspection=False)
    return TestClient(app, headers=SSE_HEADER)


def test_sse_headers(sse_client):
    response = sse_client.post("/", json={"query": "subscription { ping }"})
    assert response.status_code == HTTPStatus.OK
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["Connection"] == "keep-alive"
    assert response.headers["Transfer-Encoding"] == "chunked"
    assert response.headers["X-Accel-Buffering"] == "no"


def test_field_can_be_subscribed_to_using_sse(sse_client):
    response = sse_client.post("/", json={"query": "subscription { ping }"})
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"]["data"] == {"ping": "pong"}
    assert events[1]["event"] == "complete"


def test_non_subscription_query_cannot_be_executed_using_sse(
    sse_client,
):
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
    response = sse_client.post("/", json={"query": "query Invalid { error other }"})
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"].get("errors") is not None


def test_custom_query_parser_is_used_for_subscription_over_sse(schema):
    mock_parser = Mock(return_value=parse("subscription { testContext }"))
    app = GraphQL(
        schema,
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
    mock_validator = Mock(return_value=errors)
    app = GraphQL(
        schema,
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
    app = GraphQL(None)

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
    assert len(events) == 2
    assert (
        events[0]["data"]["errors"][0]["message"]
        == "schema is not set, call configure method to initialize it"
    )


def test_ping_is_send_sse(sse_client):
    response = sse_client.post("/", json={"query": "subscription { testSlow }"})
    events = get_sse_events(response)
    assert len(events) == 4
    assert events[0]["event"] == "next"
    assert events[0]["data"]["data"] == {"testSlow": "slow"}
    assert events[1]["event"] == "next"
    assert events[1]["data"] is None
    assert events[2]["event"] == "next"
    assert events[2]["data"]["data"] == {"testSlow": "slow"}
    assert events[3]["event"] == "complete"


def test_resolver_error_is_handled_sse(sse_client):
    response = sse_client.post("/", json={"query": "subscription { resolverError }"})
    events = get_sse_events(response)
    assert len(events) == 2
    assert events[0]["data"]["errors"][0]["message"] == "Test exception"
    assert events[1]["event"] == "complete"
