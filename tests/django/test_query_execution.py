import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from ariadne.contrib.django.views import GraphQLView


@pytest.fixture
def view(schema):
    return GraphQLView.as_view(schema=schema)


def test_post_request_fails_if_request_content_type_is_not_json(
    view, request_factory, snapshot
):
    request = request_factory.post("/graphql/", content_type="text/plain")
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)


def test_post_request_fails_if_request_data_is_malformed_json(
    view, request_factory, snapshot
):
    request = request_factory.post(
        "/graphql/", data="{malformed", content_type="application/json"
    )
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)


def test_query_in_valid_post_request_is_executed(view, request_factory, snapshot):
    request = request_factory.post(
        "/graphql/", data={"query": "{ status }"}, content_type="application/json"
    )
    response = view(request)
    assert response.status_code == 200
    snapshot.assert_match(response.content)


def test_query_is_executed_for_multipart_form_request_with_file(
    view, request_factory, snapshot
):
    request = request_factory.post(
        "/",
        {
            "operations": json.dumps(
                {
                    "query": "mutation($file: Upload!) { upload(file: $file) }",
                    "variables": {"file": None},
                }
            ),
            "map": json.dumps({"0": ["variables.file"]}),
            "0": SimpleUploadedFile("test.txt", b"test"),
        },
    )
    response = view(request)
    assert response.status_code == 200
    snapshot.assert_match(response.content)


def test_multipart_form_request_fails_if_operations_is_not_valid_json(
    view, request_factory, snapshot
):
    request = request_factory.post(
        "/",
        {
            "operations": "not a valid json",
            "map": json.dumps({"0": ["variables.file"]}),
            "0": SimpleUploadedFile("test.txt", b"test"),
        },
    )
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)


def test_multipart_form_request_fails_if_map_is_not_valid_json(
    view, request_factory, snapshot
):
    request = request_factory.post(
        "/",
        {
            "operations": json.dumps(
                {
                    "query": "mutation($file: Upload!) { upload(file: $file) }",
                    "variables": {"file": None},
                }
            ),
            "map": "not a valid json",
            "0": SimpleUploadedFile("test.txt", b"test"),
        },
    )
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)


def test_post_request_fails_for_introspection_when_disabled(
    schema, request_factory, snapshot
):
    view = GraphQLView.as_view(schema=schema, introspection=False)
    request = request_factory.post(
        "/graphql/",
        data={"query": "{ __schema { types { name } } }"},
        content_type="application/json",
    )
    response = view(request)
    assert response.status_code == 400
    snapshot.assert_match(response.content)
