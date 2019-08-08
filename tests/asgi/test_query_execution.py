import json

from starlette.testclient import TestClient

from ariadne.asgi import (
    GQL_CONNECTION_ACK,
    GQL_ERROR,
    GQL_CONNECTION_INIT,
    GQL_START,
    GraphQL,
)
from ariadne.types import Extension


operation_name = "SayHello"
variables = {"name": "Bob"}
complex_query = """
  query SayHello($name: String!) {
    hello(name: $name)
  }
"""


def test_query_is_executed_for_post_json_request(client, snapshot):
    response = client.post("/", json={"query": "{ status }"})
    assert response.status_code == 200
    snapshot.assert_match(response.json())


def test_complex_query_is_executed_for_post_json_request(client, snapshot):
    response = client.post(
        "/",
        json={
            "query": complex_query,
            "variables": variables,
            "operationName": operation_name,
        },
    )
    assert response.status_code == 200
    snapshot.assert_match(response.json())


def test_complex_query_without_operation_name_executes_successfully(client, snapshot):
    response = client.post("/", json={"query": complex_query, "variables": variables})
    assert response.status_code == 200
    snapshot.assert_match(response.json())


def test_attempt_execute_complex_query_without_variables_returns_error_json(
    client, snapshot
):
    response = client.post(
        "/", json={"query": complex_query, "operationName": operation_name}
    )
    assert response.status_code == 200
    snapshot.assert_match(response.json())


def test_attempt_execute_query_without_query_entry_returns_error_json(client, snapshot):
    response = client.post("/", json={"variables": variables})
    assert response.status_code == 400
    snapshot.assert_match(response.json())


def test_attempt_execute_query_with_non_string_query_returns_error_json(
    client, snapshot
):
    response = client.post("/", json={"query": {"test": "error"}})
    assert response.status_code == 400
    snapshot.assert_match(response.json())


def test_attempt_execute_query_with_invalid_variables_returns_error_json(
    client, snapshot
):
    response = client.post("/", json={"query": complex_query, "variables": "invalid"})
    assert response.status_code == 400
    snapshot.assert_match(response.json())


def test_attempt_execute_query_with_invalid_operation_name_string_returns_error_json(
    client, snapshot
):
    response = client.post(
        "/",
        json={
            "query": complex_query,
            "variables": variables,
            "operationName": "otherOperation",
        },
    )
    assert response.status_code == 200
    snapshot.assert_match(response.json())


def test_attempt_execute_query_with_invalid_operation_name_type_returns_error_json(
    client, snapshot
):
    response = client.post(
        "/",
        json={
            "query": complex_query,
            "variables": variables,
            "operationName": [1, 2, 3],
        },
    )
    assert response.status_code == 400
    snapshot.assert_match(response.json())


def test_attempt_execute_subscription_with_invalid_query_returns_error_json(
    client, snapshot
):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { error }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_ERROR
        snapshot.assert_match(response["payload"])


def test_query_is_executed_for_multipart_form_request_with_file(client, snapshot):
    response = client.post(
        "/",
        data={
            "operations": json.dumps(
                {
                    "query": "mutation($file: Upload!) { upload(file: $file) }",
                    "variables": {"file": None},
                }
            ),
            "map": json.dumps({"0": ["variables.file"]}),
        },
        files={"0": ("test.txt", "hello")},
    )
    assert response.status_code == 200
    snapshot.assert_match(response.json())


class CustomExtension(Extension):
    async def resolve(self, next_, parent, info, **kwargs):
        value = next_(parent, info, **kwargs)
        return f"={value}="


def test_middlewares_and_extensions_are_combined_in_correct_order(schema):
    def test_middleware(next_fn, *args, **kwargs):
        value = next_fn(*args, **kwargs)
        return f"*{value}*"

    app = GraphQL(schema, extensions=[CustomExtension], middleware=[test_middleware])
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "=*Hello, BOB!*="}}
