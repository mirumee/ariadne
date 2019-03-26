# pylint: disable=too-many-arguments
from ariadne.constants import HTTP_STATUS_200_OK, HTTP_STATUS_400_BAD_REQUEST

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
