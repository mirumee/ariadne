from unittest.mock import Mock

import pytest

from ariadne import GraphQLMiddleware, HttpError

type_defs = """
    type Query {
        test: String
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
    return GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers={})


@pytest.fixture
def server():
    return GraphQLMiddleware(None, type_defs=type_defs, resolvers={}, path="/")


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


def test_http_errors_raised_in_handle_request_are_passed_to_error_handler(
    server, start_response
):
    exception = HttpError()
    server.handle_request = Mock(side_effect=exception)
    server.handle_http_error = Mock()
    server({"PATH_INFO": "/"}, start_response)

    server.handle_http_error.assert_called_once_with(start_response, exception)
