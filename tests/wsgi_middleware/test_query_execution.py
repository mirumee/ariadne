# pylint: disable=too-many-arguments

operation_name = "SayHello"
variables = {"name": "Bob"}
complex_query = """
  query SayHello($name: String!) {
    hello(name: $name)
  }
"""


def test_query_is_executed_for_post_json_request(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(query="{ status }")
    result = middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    assert_json_response_equals_snapshot(result)


def test_complex_query_is_executed_for_post_json_request(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(
        query=complex_query, variables=variables, operationName=operation_name
    )
    result = middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    assert_json_response_equals_snapshot(result)


def test_complex_query_without_operation_name_executes_successfully(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(query=complex_query, variables=variables)
    result = middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    assert_json_response_equals_snapshot(result)


def test_attempt_execute_complex_query_without_variables_returns_error_json(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    failed_query_http_status,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(
        query=complex_query, operationName=operation_name
    )
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)


def test_attempt_execute_query_without_query_entry_returns_error_json(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    failed_query_http_status,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(variables=variables)
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)


def test_attempt_execute_query_with_non_string_query_returns_error_json(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    failed_query_http_status,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(query={"test": "error"})
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)


def test_attempt_execute_query_with_invalid_variables_returns_error_json(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    failed_query_http_status,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(query=complex_query, variables="invalid")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)


def test_attempt_execute_query_with_invalid_operation_name_returns_error_json(
    middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    failed_query_http_status,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(
        query=complex_query, variables=variables, operationName=[1, 2, 3]
    )
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    assert_json_response_equals_snapshot(result)
