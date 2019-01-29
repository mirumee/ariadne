from wsgiref import simple_server

import pytest

from ariadne import make_executable_schema, start_simple_server
from ariadne.wsgi import GraphQL


@pytest.fixture
def simple_server_mock(mocker):
    return mocker.Mock(serve_forever=mocker.Mock(return_value=True))


@pytest.fixture
def middleware_make_simple_server_mock(mocker):
    return mocker.patch.object(simple_server, "make_server", new=mocker.Mock())


@pytest.fixture
def type_defs():
    return """
        type Query {
            hello: String
        }
    """


@pytest.fixture
def resolvers():
    return []


@pytest.fixture
def schema(type_defs, resolvers):
    return make_executable_schema(type_defs, resolvers)


def test_wsgi_simple_server_serve_forever_is_called(mocker, schema, simple_server_mock):
    mocker.patch("wsgiref.simple_server.make_server", return_value=simple_server_mock)
    start_simple_server(schema)
    simple_server_mock.serve_forever.assert_called_once()


def test_keyboard_interrupt_is_handled_gracefully(mocker, schema):
    mocker.patch(
        "wsgiref.simple_server.make_server", side_effect=KeyboardInterrupt("test")
    )
    start_simple_server(schema)


def test_type_defs_resolvers_host_and_ip_are_passed_to_graphql_middleware(
    middleware_make_simple_server_mock, schema
):
    start_simple_server(schema, host="0.0.0.0", port=4444)
    call = middleware_make_simple_server_mock.call_args[0]
    assert call[0] == "0.0.0.0"
    assert call[1] == 4444
    assert isinstance(call[2], GraphQL)


def test_default_host_and_ip_are_passed_to_graphql_middleware_if_not_set(
    middleware_make_simple_server_mock, schema
):
    start_simple_server(schema)
    call = middleware_make_simple_server_mock.call_args[0]
    assert call[0] == "127.0.0.1"
    assert call[1] == 8888
    assert isinstance(call[2], GraphQL)


def test_default_host_and_ip_are_printed_on_server_creation(
    middleware_make_simple_server_mock, capsys
):  # pylint: disable=unused-argument
    schema = make_executable_schema("type Query { dummy: Boolean }", {})
    start_simple_server(schema)
    captured = capsys.readouterr()
    assert "http://127.0.0.1:8888" in captured.out


def test_custom_host_and_ip_are_printed_on_server_creation(
    middleware_make_simple_server_mock, capsys
):  # pylint: disable=unused-argument
    schema = make_executable_schema("type Query { dummy: Boolean }", {})
    start_simple_server(schema, host="0.0.0.0", port=4444)
    captured = capsys.readouterr()
    assert "http://0.0.0.0:4444" in captured.out
