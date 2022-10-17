from starlette.testclient import TestClient

from ariadne.explorer import (
    ExplorerApollo,
    ExplorerGraphiQL,
    ExplorerHttp405,
    ExplorerPlayground,
)
from ariadne.asgi import GraphQL


def test_default_explorer_html_is_served_on_get_request(schema, snapshot):
    app = GraphQL(schema)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    snapshot.assert_match(response.text)


def test_apollo_html_is_served_on_get_request(schema, snapshot):
    app = GraphQL(schema, explorer=ExplorerApollo())
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    snapshot.assert_match(response.text)


def test_graphiql_html_is_served_on_get_request(schema, snapshot):
    app = GraphQL(schema, explorer=ExplorerGraphiQL())
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    snapshot.assert_match(response.text)


def test_playground_html_is_served_on_get_request(schema, snapshot):
    app = GraphQL(schema, explorer=ExplorerPlayground())
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    snapshot.assert_match(response.text)


def test_405_bad_method_is_served_on_get_request_for_disabled_explorer(
    schema, snapshot
):
    app = GraphQL(schema, explorer=ExplorerHttp405())
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 405
    snapshot.assert_match(response.text)
