from starlette.testclient import TestClient

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler


def test_options_method_is_supported(client):
    response = client.options("/")
    assert response.status_code == 200
    assert response.headers["Allow"] == "OPTIONS, POST, GET"


def test_options_response_excludes_get_if_introspection_is_disabled(schema):
    handler = GraphQLHTTPHandler(schema, introspection=False)
    app = GraphQL(handler)
    client = TestClient(app)

    response = client.options("/")
    assert response.status_code == 200
    assert response.headers["Allow"] == "OPTIONS, POST"


def test_patch_is_not_supported(client):
    response = client.patch("/", json={})
    assert response.status_code == 405
    assert response.headers["Allow"] == "OPTIONS, POST, GET"


def test_put_is_not_supported(client):
    response = client.put("/", json={})
    assert response.status_code == 405
    assert response.headers["Allow"] == "OPTIONS, POST, GET"


def test_delete_is_not_supported(client):
    response = client.delete("/", json={})
    assert response.status_code == 405
    assert response.headers["Allow"] == "OPTIONS, POST, GET"


def test_unsupported_method_response_excludes_get_if_introspection_is_disabled(schema):
    handler = GraphQLHTTPHandler(schema, introspection=False)
    app = GraphQL(handler)
    client = TestClient(app)

    response = client.patch("/")
    assert response.status_code == 405
    assert response.headers["Allow"] == "OPTIONS, POST"
