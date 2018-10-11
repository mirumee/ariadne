import json
from io import StringIO
from unittest.mock import Mock

import pytest

from ariadne import (
    GraphQLMiddleware,
    HttpError,
    HttpBadRequestError,
    HttpMethodNotAllowedError,
)

type_defs = """
    type Query {
        hello(name: String): String
        status: Boolean
    }
"""


def resolve_hello(*_, name):
    return "Hello, %s!" % name


def resolve_status(*_):
    return True


resolvers = {"Query": {"hello": resolve_hello, "status": resolve_status}}

graphql_response_headers = [("Content-Type", "application/json; charset=UTF-8")]
error_response_headers = [("Content-Type", "text/plain; charset=UTF-8")]
playground_response_headers = [("Content-Type", "text/html; charset=UTF-8")]

failed_query_http_status = "400 Bad Request"

operation_name = "SayHello"
variables = {"name": "Bob"}
complex_query = """
  query SayHello($name: String!) {
    hello(name: $name)
  }
"""


@pytest.fixture
def app_mock():
    return Mock(return_value=True)


@pytest.fixture
def start_response():
    return Mock()


@pytest.fixture
def middleware(app_mock):
    return GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers=resolvers)


@pytest.fixture
def server():
    return GraphQLMiddleware(None, type_defs=type_defs, resolvers=resolvers, path="/")


@pytest.fixture
def middleware_request():
    return {"PATH_INFO": "/graphql/"}


@pytest.fixture
def graphql_query_request_factory(middleware_request):
    def wrapped_graphql_query_request_factory(
        raw_data=None,
        query=None,
        operationName=None,
        variables=None,
        content_length=None,
    ):
        data = {}
        if query:
            data["query"] = query
        if operationName:
            data["operationName"] = operationName
        if variables:
            data["variables"] = variables
        data_json = json.dumps(data)

        middleware_request.update(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "application/json",
                "CONTENT_LENGTH": content_length or len(data_json),
                "wsgi.input": StringIO(data_json if data else raw_data),
            }
        )
        return middleware_request

    return wrapped_graphql_query_request_factory


def test_initializing_middleware_without_path_raises_value_error():
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(None, type_defs=type_defs, resolvers={}, path="")

    assert isinstance(excinfo.value, ValueError)
    assert excinfo.value.args[0] == "path keyword argument can't be empty"


def test_initializing_middleware_with_non_callable_app_raises_type_error():
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(True, type_defs=type_defs, resolvers={}, path="/")
    assert isinstance(excinfo.value, TypeError)
    assert excinfo.value.args[0] == "first argument must be a callable or None"


def test_initializing_middleware_without_app_raises_type_error():
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(None, type_defs=type_defs, resolvers={})
    assert isinstance(excinfo.value, TypeError)
    assert excinfo.value.args[0] == (
        "can't set custom path on WSGI middleware without providing "
        "application callable as first argument"
    )


def test_initializing_middleware_with_app_and_root_path_raises_value_error(app_mock):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers={}, path="/")
    assert isinstance(excinfo.value, ValueError)
    assert excinfo.value.args[0] == (
        "WSGI middleware can't use root path together with application callable"
    )


def test_request_to_app_root_path_is_forwarded(app_mock, middleware):
    middleware({"PATH_INFO": "/"}, Mock())
    assert app_mock.called


def test_request_to_app_sub_path_is_forwarded(app_mock, middleware):
    middleware({"PATH_INFO": "/something/"}, Mock())
    assert app_mock.called


def test_request_to_graphql_path_is_handled(app_mock, middleware):
    middleware.handle_request = Mock()
    middleware({"PATH_INFO": "/graphql/"}, Mock())
    assert middleware.handle_request.called
    assert not app_mock.called


def test_app_exceptions_are_not_handled(app_mock):
    exception = Exception("Test exception")
    app_mock = Mock(side_effect=exception)
    middleware = GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers={})
    middleware.handle_request = Mock()

    with pytest.raises(Exception) as excinfo:
        middleware({"PATH_INFO": "/"}, Mock())
    assert excinfo.value is exception
    assert not middleware.handle_request.called


def test_request_to_graphql_server_root_path_is_handled(server):
    server.handle_request = Mock()
    server({"PATH_INFO": "/"}, Mock())
    assert server.handle_request.called


def test_request_to_graphql_server_sub_path_is_handled(server):
    server.handle_request = Mock()
    server({"PATH_INFO": "/something/"}, Mock())
    assert server.handle_request.called


def test_http_errors_raised_in_handle_request_are_passed_to_http_error_handler(
    middleware, middleware_request, start_response
):
    exception = HttpError()
    middleware.handle_request = Mock(side_effect=exception)
    middleware.handle_http_error = Mock()
    middleware(middleware_request, start_response)

    middleware.handle_http_error.assert_called_once_with(start_response, exception)


def test_http_error_400_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response
):
    exception = HttpBadRequestError()
    middleware.handle_request = Mock(side_effect=exception)

    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [exception.status.encode("utf-8")]


def test_http_error_400_with_message_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response
):
    message = "This is bad request error."
    exception = HttpBadRequestError(message)
    middleware.handle_request = Mock(side_effect=exception)

    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [message.encode("utf-8")]


def test_http_error_405_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response
):
    exception = HttpMethodNotAllowedError()
    middleware.handle_request = Mock(side_effect=exception)

    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [exception.status.encode("utf-8")]


def test_http_error_405_with_message_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response
):
    message = "This is method not allowed error."
    exception = HttpMethodNotAllowedError(message)
    middleware.handle_request = Mock(side_effect=exception)

    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [message.encode("utf-8")]


def test_get_handler_is_called_for_for_get_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "GET"
    middleware.handle_get = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_get.assert_called_once_with(start_response)


def test_post_handler_is_called_for_for_post_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "POST"
    middleware.handle_post = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_post.assert_called_once_with(middleware_request, start_response)


def test_http_not_allowed_error_is_thrown_for_delete_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "DELETE"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_http_error.assert_called_once()


def test_http_not_allowed_error_is_thrown_for_head_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "HEAD"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_http_error.assert_called_once()


def test_http_not_allowed_error_is_thrown_for_patch_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PATCH"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_http_error.assert_called_once()


def test_http_not_allowed_error_is_thrown_for_put_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PUT"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_http_error.assert_called_once()


def test_http_not_allowed_error_is_thrown_for_options_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "OPTIONS"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    middleware.handle_http_error.assert_called_once()


def test_query_is_executed_for_post_json_request(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(query="{ status }")
    result = middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    snapshot.assert_match(result)


def test_complex_query_is_executed_for_post_json_request(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(
        query=complex_query, variables=variables, operationName=operation_name
    )
    result = middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    snapshot.assert_match(result)


def test_execute_complex_query_without_operation_name(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(query=complex_query, variables=variables)
    result = middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    snapshot.assert_match(result)


def test_attempt_execute_complex_query_without_variables(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(
        query=complex_query, operationName=operation_name
    )
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    snapshot.assert_match(result)


def test_attempt_execute_query_without_query_entry(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(variables=variables)
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    snapshot.assert_match(result)


def test_attempt_execute_query_with_invalid_variables(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(query=complex_query, variables="invalid")
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, error_response_headers
    )
    snapshot.assert_match(result)


def test_attempt_execute_query_with_invalid_operation_name(
    middleware, start_response, snapshot, graphql_query_request_factory
):
    request = graphql_query_request_factory(
        query=complex_query, variables=variables, operationName=[1, 2, 3]
    )
    result = middleware(request, start_response)
    start_response.assert_called_once_with(
        failed_query_http_status, graphql_response_headers
    )
    snapshot.assert_match(result)
