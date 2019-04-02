import pytest

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


@pytest.fixture
def app(schema):
    return GraphQL(schema)


@pytest.fixture
def client(app):
    return TestClient(app)
