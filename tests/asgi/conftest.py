import pytest

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL
from ariadne.contrib.tracing.opentracing import opentracing_extension


@pytest.fixture
def app(schema):
    return GraphQL(schema)


@pytest.fixture
def app_with_tracing(schema):
    def dummy_filter(args, _):
        return args

    return GraphQL(schema, extensions=[opentracing_extension(arg_filter=dummy_filter)])


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def client_for_tracing(app_with_tracing):
    return TestClient(app_with_tracing)
