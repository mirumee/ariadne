from unittest.mock import Mock

import pytest

from ariadne import GraphQLMiddleware
from ariadne.exceptions import HttpMethodNotAllowedError


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


def test_request_to_graphql_server_root_path_is_handled(server):
    server.handle_request = Mock()
    server({"PATH_INFO": "/"}, Mock())
    assert server.handle_request.called


def test_request_to_graphql_server_sub_path_is_handled(server):
    server.handle_request = Mock()
    server({"PATH_INFO": "/something/"}, Mock())
    assert server.handle_request.called


def test_app_exceptions_are_not_handled(app_mock, type_defs):
    exception = Exception("Test exception")
    app_mock = Mock(side_effect=exception)
    middleware = GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers={})
    middleware.handle_request = Mock()

    with pytest.raises(Exception) as excinfo:
        middleware({"PATH_INFO": "/"}, Mock())
    assert excinfo.value is exception
    assert not middleware.handle_request.called


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
    assert middleware.handle_http_error.call_count == 1
    called_with_args = middleware.handle_http_error.call_args[0]
    assert len(called_with_args) == 2
    assert isinstance(called_with_args[0], HttpMethodNotAllowedError)
    assert called_with_args[1] == start_response


def test_http_not_allowed_error_is_thrown_for_head_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "HEAD"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    assert middleware.handle_http_error.call_count == 1
    called_with_args = middleware.handle_http_error.call_args[0]
    assert len(called_with_args) == 2
    assert isinstance(called_with_args[0], HttpMethodNotAllowedError)
    assert called_with_args[1] == start_response


def test_http_not_allowed_error_is_thrown_for_patch_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PATCH"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    assert middleware.handle_http_error.call_count == 1
    called_with_args = middleware.handle_http_error.call_args[0]
    assert len(called_with_args) == 2
    assert isinstance(called_with_args[0], HttpMethodNotAllowedError)
    assert called_with_args[1] == start_response


def test_http_not_allowed_error_is_thrown_for_put_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PUT"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    assert middleware.handle_http_error.call_count == 1
    called_with_args = middleware.handle_http_error.call_args[0]
    assert len(called_with_args) == 2
    assert isinstance(called_with_args[0], HttpMethodNotAllowedError)
    assert called_with_args[1] == start_response


def test_http_not_allowed_error_is_thrown_for_options_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "OPTIONS"
    middleware.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    assert middleware.handle_http_error.call_count == 1
    called_with_args = middleware.handle_http_error.call_args[0]
    assert len(called_with_args) == 2
    assert isinstance(called_with_args[0], HttpMethodNotAllowedError)
    assert called_with_args[1] == start_response
