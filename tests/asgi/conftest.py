import pytest

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import (
    GraphQLHTTPHandler,
    GraphQLTransportWSHandler,
    GraphQLWSHandler,
)
from ariadne.contrib.tracing.opentracing import opentracing_extension


@pytest.fixture
def app(schema):
    http_handler = GraphQLHTTPHandler(schema)
    subscription_handler = GraphQLWSHandler(schema, http_handler=http_handler)
    return GraphQL(http_handler=http_handler, subscription_handler=subscription_handler)


@pytest.fixture
def app_graphql_ws_no_http(schema):
    subscription_handler = GraphQLWSHandler(schema)
    return GraphQL(subscription_handler=subscription_handler)


@pytest.fixture
def app_graphql_ws_keepalive(schema):
    http_handler = GraphQLHTTPHandler(schema)
    subscription_handler = GraphQLWSHandler(
        schema, keepalive=1, http_handler=http_handler
    )
    return GraphQL(http_handler=http_handler, subscription_handler=subscription_handler)


@pytest.fixture
def app_graphql_transport_ws(schema):
    http_handler = GraphQLHTTPHandler(schema)
    subscription_handler = GraphQLTransportWSHandler(schema, http_handler=http_handler)
    return GraphQL(http_handler=http_handler, subscription_handler=subscription_handler)


@pytest.fixture
def app_graphql_transport_ws_no_http(schema):
    subscription_handler = GraphQLTransportWSHandler(schema)
    return GraphQL(subscription_handler=subscription_handler)


@pytest.fixture
def app_with_tracing(schema):
    def dummy_filter(args, _):
        return args

    handler = GraphQLHTTPHandler(
        schema, extensions=[opentracing_extension(arg_filter=dummy_filter)]
    )
    subscription_handler = GraphQLWSHandler(schema)
    return GraphQL(http_handler=handler, subscription_handler=subscription_handler)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def client_graphql_ws_no_http(app_graphql_ws_no_http):
    return TestClient(app_graphql_ws_no_http)


@pytest.fixture
def client_graphql_ws_keepalive(app_graphql_ws_keepalive):
    return TestClient(app_graphql_ws_keepalive)


@pytest.fixture
def client_graphql_transport_ws(app_graphql_transport_ws):
    return TestClient(app_graphql_transport_ws)


@pytest.fixture
def client_graphql_transport_ws_no_http(app_graphql_transport_ws_no_http):
    return TestClient(app_graphql_transport_ws_no_http)


@pytest.fixture
def client_for_tracing(app_with_tracing):
    return TestClient(app_with_tracing)
