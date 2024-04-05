from http import HTTPStatus

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


def test_options_method_is_supported(client):
    response = client.options("/")
    assert response.status_code == HTTPStatus.OK
    assert response.headers["Allow"] == "OPTIONS, POST, GET"


def test_options_response_excludes_get_if_introspection_is_disabled(schema):
    app = GraphQL(schema, introspection=False)
    client = TestClient(app)

    response = client.options("/")
    assert response.status_code == HTTPStatus.OK
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
    response = client.delete("/")
    assert response.status_code == 405
    assert response.headers["Allow"] == "OPTIONS, POST, GET"


def test_unsupported_method_response_excludes_get_if_introspection_is_disabled(schema):
    app = GraphQL(schema, introspection=False)
    client = TestClient(app)

    response = client.patch("/")
    assert response.status_code == 405
    assert response.headers["Allow"] == "OPTIONS, POST"
