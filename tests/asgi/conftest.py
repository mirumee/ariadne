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
    return GraphQL(schema)


@pytest.fixture
def app_graphql_ws_keepalive(schema):
    websocket_handler = GraphQLWSHandler(keepalive=1)
    return GraphQL(schema, websocket_handler=websocket_handler)


@pytest.fixture
def app_graphql_transport_ws(schema):
    websocket_handler = GraphQLTransportWSHandler()
    return GraphQL(schema, websocket_handler=websocket_handler)


@pytest.fixture
def app_with_tracing(schema):
    def dummy_filter(args, _):
        return args

    handler = GraphQLHTTPHandler(
        extensions=[opentracing_extension(arg_filter=dummy_filter)]
    )
    return GraphQL(schema, http_handler=handler)


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def client_graphql_ws_keepalive(app_graphql_ws_keepalive):
    return TestClient(app_graphql_ws_keepalive)


@pytest.fixture
def client_graphql_transport_ws(app_graphql_transport_ws):
    return TestClient(app_graphql_transport_ws)


@pytest.fixture
def client_for_tracing(app_with_tracing):
    return TestClient(app_with_tracing)
