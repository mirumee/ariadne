import json
from io import StringIO

import pytest

from ariadne import HttpBadRequestError


@pytest.fixture
def assert_start_response_called_once_with_bad_request_error(error_response_headers):
    def assertion(start_response):
        assert start_response.called
        assert start_response.call_count == 1

        called_with_args = start_response.call_args[0]
        assert len(called_with_args) == 2
        assert called_with_args == (HttpBadRequestError.status, error_response_headers)

    return assertion


@pytest.fixture
def assert_start_response_called_once_with_graphql_error(graphql_response_headers):
    def assertion(start_response):
        assert start_response.called
        assert start_response.call_count == 1

        called_with_args = start_response.call_args[0]
        assert len(called_with_args) == 2
        assert called_with_args == (
            HttpBadRequestError.status,
            graphql_response_headers,
        )

    return assertion


def test_attempt_parse_request_missing_content_type_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory()
    request.pop("CONTENT_TYPE")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_parse_non_json_request_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory(content_type="text/plain")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_get_content_length_from_missing_header_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory()
    request.pop("CONTENT_LENGTH")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_get_content_length_from_malformed_header_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory(content_length="malformed")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_get_request_body_from_missing_wsgi_input_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory()
    request.pop("wsgi.input")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_get_request_body_from_empty_wsgi_input_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory()
    request["wsgi.input"] = StringIO("")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_parse_non_json_request_body_raises_bad_request_error(
    middleware,
    start_response,
    snapshot,
    graphql_query_request_factory,
    assert_start_response_called_once_with_bad_request_error,
):
    request = graphql_query_request_factory(raw_data="not-json")
    result = middleware(request, start_response)
    snapshot.assert_match(result)
    assert_start_response_called_once_with_bad_request_error(start_response)


def test_attempt_parse_json_scalar_request_raises_graphql_bad_request_error(
    middleware,
    start_response,
    graphql_query_request_factory,
    assert_json_response_equals_snapshot,
    assert_start_response_called_once_with_graphql_error,
):
    request = graphql_query_request_factory(raw_data=json.dumps("json string"))
    result = middleware(request, start_response)
    assert_json_response_equals_snapshot(result)
    assert_start_response_called_once_with_graphql_error(start_response)


def test_attempt_parse_json_array_request_raises_graphql_bad_request_error(
    middleware,
    start_response,
    graphql_query_request_factory,
    assert_json_response_equals_snapshot,
    assert_start_response_called_once_with_graphql_error,
):
    request = graphql_query_request_factory(raw_data=json.dumps([1, 2, 3]))
    result = middleware(request, start_response)
    assert_json_response_equals_snapshot(result)
    assert_start_response_called_once_with_graphql_error(start_response)
