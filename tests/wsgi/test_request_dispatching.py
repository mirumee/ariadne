from unittest.mock import Mock

import pytest

from ariadne.constants import (
    CONTENT_TYPE_TEXT_PLAIN,
    HttpStatusResponse,
)
from ariadne.wsgi import GraphQL, GraphQLMiddleware


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
    handle_get.assert_called_once_with(middleware_request, start_response)


def test_post_handler_is_called_for_post_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "POST"
    handle_post = middleware.graphql_app.handle_post = Mock()

    middleware(middleware_request, start_response)
    handle_post.assert_called_once_with(middleware_request, start_response)


def test_allowed_methods_list_is_returned_for_options_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "OPTIONS"
    middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.OK.value,
        [
            ("Content-Type", CONTENT_TYPE_TEXT_PLAIN),
            ("Content-Length", 0),
            ("Allow", "OPTIONS, POST, GET"),
        ],
    )


def test_allowed_methods_list_returned_for_options_request_excludes_get(
    app_mock, middleware_request, start_response, schema
):
    middleware_request["REQUEST_METHOD"] = "OPTIONS"
    server = GraphQL(schema, introspection=False)
    middleware = GraphQLMiddleware(app_mock, server)
    middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.OK.value,
        [
            ("Content-Type", CONTENT_TYPE_TEXT_PLAIN),
            ("Content-Length", 0),
            ("Allow", "OPTIONS, POST"),
        ],
    )


METHOD_NOT_ALLOWED_HEADERS = [
    ("Content-Type", CONTENT_TYPE_TEXT_PLAIN),
    ("Content-Length", 0),
    ("Allow", "OPTIONS, POST, GET"),
]


def test_http_not_allowed_response_is_returned_for_delete_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "DELETE"
    middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.METHOD_NOT_ALLOWED.value, METHOD_NOT_ALLOWED_HEADERS
    )


def test_http_not_allowed_response_is_returned_for_head_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "HEAD"
    middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.METHOD_NOT_ALLOWED.value, METHOD_NOT_ALLOWED_HEADERS
    )


def test_http_not_allowed_response_is_returned_for_patch_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PATCH"
    middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.METHOD_NOT_ALLOWED.value, METHOD_NOT_ALLOWED_HEADERS
    )


def test_http_not_allowed_response_is_returned_for_put_request(
    middleware, middleware_request, start_response
):
    middleware_request["REQUEST_METHOD"] = "PUT"
    middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HttpStatusResponse.METHOD_NOT_ALLOWED.value, METHOD_NOT_ALLOWED_HEADERS
    )
