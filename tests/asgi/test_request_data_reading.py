import json
from http import HTTPStatus


def test_attempt_parse_request_missing_content_type_raises_bad_request_error(
    client, snapshot
):
    response = client.post("/", content="")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.text


def test_attempt_parse_non_json_request_raises_bad_request_error(client, snapshot):
    response = client.post("/", content="", headers={"content-type": "text/plain"})
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.text


def test_attempt_parse_non_json_request_body_raises_bad_request_error(client, snapshot):
    response = client.post(
        "/", content="", headers={"content-type": "application/json"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.text


def test_attempt_parse_json_scalar_request_raises_graphql_bad_request_error(
    client, snapshot
):
    response = client.post("/", json="json string")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.text


def test_attempt_parse_json_array_request_raises_graphql_bad_request_error(
    client, snapshot
):
    response = client.post("/", json=[1, 2, 3])
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.text


def test_multipart_form_request_fails_if_operations_is_not_valid_json(client, snapshot):
    response = client.post(
        "/",
        data={
            "operations": "not a valid json",
            "map": json.dumps({"0": ["variables.file"]}),
        },
        files={"0": ("test.txt", b"hello")},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.content


def test_multipart_form_request_fails_if_map_is_not_valid_json(client, snapshot):
    response = client.post(
        "/",
        data={
            "operations": json.dumps(
                {
                    "query": "mutation($file: Upload!) { upload(file: $file) }",
                    "variables": {"file": None},
                }
            ),
            "map": "not a valid json",
        },
        files={"0": ("test.txt", b"hello")},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert snapshot == response.content
