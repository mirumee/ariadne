from starlette.testclient import TestClient

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler


def test_playground_html_is_served_on_get_request(schema, snapshot):
    handler = GraphQLHTTPHandler(schema)
    app = GraphQL(handler)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    snapshot.assert_match(response.text)
