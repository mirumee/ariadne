import json
from io import BytesIO

from ariadne.constants import HttpStatusResponse
from ariadne.exceptions import HttpBadRequestError

from .factories import create_multipart_request


def test_attempt_parse_request_missing_content_type_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory()
    request.pop("CONTENT_TYPE")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_parse_non_json_request_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory(content_type="text/plain")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_get_content_length_from_missing_header_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory()
    request.pop("CONTENT_LENGTH")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_get_content_length_from_malformed_header_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory(content_length="malformed")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_get_request_body_from_missing_wsgi_input_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory()
    request.pop("wsgi.input")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_get_request_body_from_empty_wsgi_input_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory()
    request["wsgi.input"] = BytesIO(b"")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_parse_non_json_request_body_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    error_response_headers,
):
    request = graphql_query_request_factory(raw_data="not-json")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, error_response_headers
    )
    assert snapshot == result


def test_attempt_parse_json_scalar_request_raises_graphql_bad_request_error(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(raw_data=json.dumps("json string"))
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)


def test_attempt_parse_json_array_request_raises_graphql_bad_request_error(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(raw_data=json.dumps([1, 2, 3]))
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpBadRequestError().status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)


def test_multipart_form_request_fails_if_operations_is_not_valid_json(
    middleware, snapshot, start_response, error_response_headers
):
    data = """
--------------------------cec8e8123c05ba25
Content-Disposition: form-data; name="operations"

not a json
--------------------------cec8e8123c05ba25
Content-Disposition: form-data; name="map"

{ "0": ["variables.file"] }
--------------------------cec8e8123c05ba25
Content-Disposition: form-data; name="0"; filename="test.txt"
Content-Type: text/plain

test

--------------------------cec8e8123c05ba25--
    """.strip().replace("\n", "\r\n")

    request = create_multipart_request(data)
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.BAD_REQUEST.value, error_response_headers
    )
    assert snapshot == result


def test_multipart_form_request_fails_if_map_is_not_valid_json(
    middleware, snapshot, start_response, error_response_headers
):
    data = """
--------------------------cec8e8123c05ba25
Content-Disposition: form-data; name="operations"

{ "query": "mutation ($file: Upload!) { upload(file: $file) }", "variables": { "file": null } }  
--------------------------cec8e8123c05ba25
Content-Disposition: form-data; name="map"

not a json
--------------------------cec8e8123c05ba25
Content-Disposition: form-data; name="0"; filename="test.txt"
Content-Type: text/plain

test

--------------------------cec8e8123c05ba25--
    """.strip().replace(  # noqa: E501
        "\n", "\r\n"
    )

    request = create_multipart_request(data)
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.BAD_REQUEST.value, error_response_headers
    )
    assert snapshot == result
