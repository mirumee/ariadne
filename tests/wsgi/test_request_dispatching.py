from unittest.mock import Mock

import pytest

from ariadne.exceptions import HttpMethodNotAllowedError
from ariadne.wsgi import GraphQLMiddleware


def test_request_to_app_root_path_is_forwarded(app_mock, middleware):
    middleware({"PATH_INFO": "/"}, Mock())
    assert app_mock.called


def test_request_to_app_sub_path_is_forwarded(app_mock, middleware):
    middleware({"PATH_INFO": "/something/"}, Mock())
    assert app_mock.called


def test_request_to_graphql_path_is_handled(app_mock, middleware):
    handle_request = middleware.graphql_app.handle_request = Mock()
    middleware({"PATH_INFO": "/graphql/"}, Mock())
    assert handle_request.called
    assert not app_mock.called


def test_request_to_graphql_server_root_path_is_handled(server):
    server.handle_request = Mock()
    server({"PATH_INFO": "/"}, Mock())
    assert server.handle_request.called


def test_request_to_graphql_server_sub_path_is_handled(server):
    server.handle_request = Mock()
    server({"PATH_INFO": "/something/"}, Mock())
    assert server.handle_request.called


def test_app_exceptions_are_not_handled(app_mock, schema):
    exception = Exception("Test exception")
    app_mock = Mock(side_effect=exception)
    middleware = GraphQLMiddleware(app_mock, schema)
    handle_request = middleware.graphql_app.handle_request = Mock()

    with pytest.raises(Exception) as excinfo:
        middleware({"PATH_INFO": "/"}, Mock())
    assert excinfo.value is exception
    assert not handle_request.called


def test_get_handler_is_called_for_get_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "GET"
    handle_get = middleware.graphql_app.handle_get = Mock()

    middleware(middleware_request, start_response)
    handle_get.assert_called_once_with(start_response)


def test_post_handler_is_called_for_post_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "POST"
    handle_post = middleware.graphql_app.handle_post = Mock()

    middleware(middleware_request, start_response)
    handle_post.assert_called_once_with(middleware_request, start_response)


class InstanceOfHttpMethodNotAllowedError:
    def __eq__(self, other):
        return isinstance(other, HttpMethodNotAllowedError)


def test_http_not_allowed_error_is_thrown_for_delete_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "DELETE"
    handle_error = middleware.graphql_app.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    handle_error.assert_called_once_with(
        InstanceOfHttpMethodNotAllowedError(), start_response
    )


def test_http_not_allowed_error_is_thrown_for_head_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "HEAD"
    handle_error = middleware.graphql_app.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    handle_error.assert_called_once_with(
        InstanceOfHttpMethodNotAllowedError(), start_response
    )


def test_http_not_allowed_error_is_thrown_for_patch_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PATCH"
    handle_error = middleware.graphql_app.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    handle_error.assert_called_once_with(
        InstanceOfHttpMethodNotAllowedError(), start_response
    )


def test_http_not_allowed_error_is_thrown_for_put_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PUT"
    handle_error = middleware.graphql_app.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    handle_error.assert_called_once_with(
        InstanceOfHttpMethodNotAllowedError(), start_response
    )


def test_http_not_allowed_error_is_thrown_for_options_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "OPTIONS"
    handle_error = middleware.graphql_app.handle_http_error = Mock()

    middleware(middleware_request, start_response)
    handle_error.assert_called_once_with(
        InstanceOfHttpMethodNotAllowedError(), start_response
    )
