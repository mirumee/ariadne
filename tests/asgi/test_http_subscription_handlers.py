"""Tests for GraphQL HTTP handler subscription_handlers integration."""

from http import HTTPStatus

import pytest
from starlette.testclient import TestClient

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.subscription_handlers.handlers import SubscriptionHandler


class MockSubscriptionHandler(SubscriptionHandler):
    """Mock handler that records whether handle was called."""

    def __init__(self, should_support: bool = True):
        self.should_support = should_support
        self.handle_called = False

    def supports(self, request, data):
        return self.should_support and isinstance(data, dict)

    async def handle(self, request, data, **kwargs):
        self.handle_called = True
        from starlette.responses import JSONResponse

        return JSONResponse({"handled": True})


@pytest.fixture
def simple_schema():
    type_defs = """
        type Query {
            hello: String!
        }
    """
    return make_executable_schema(type_defs)


def test_graphql_http_server_returns_400_on_invalid_request_body(simple_schema):
    """
    When extract_data_from_request raises HttpError,
    return 400 and do not call handlers.
    """
    handler = MockSubscriptionHandler(should_support=True)
    app = GraphQL(
        simple_schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )
    client = TestClient(app)

    response = client.post(
        "/",
        content="not valid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert handler.handle_called is False


def test_graphql_http_server_skips_subscription_handlers_when_data_is_list(
    simple_schema,
):
    """When request data is a list (batch), subscription_handlers are not tried."""
    handler = MockSubscriptionHandler(should_support=True)
    app = GraphQL(
        simple_schema,
        http_handler=GraphQLHTTPHandler(subscription_handlers=[handler]),
    )
    client = TestClient(app)

    # Batch request: body is a list of operations.
    # Handlers require isinstance(data, dict).
    response = client.post(
        "/",
        json=[{"query": "{ __typename }"}],
        headers={"Content-Type": "application/json"},
    )

    assert handler.handle_called is False
    # Data is list so subscription_handlers block is skipped; graphql then validates
    # and rejects list data, returning 400.
    assert response.status_code == HTTPStatus.BAD_REQUEST
