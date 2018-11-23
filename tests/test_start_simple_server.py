import pytest

from ariadne import GraphQLMiddleware, start_simple_server


@pytest.fixture
def simple_server_mock(mocker):
    return mocker.Mock(serve_forever=mocker.Mock(return_value=True))


@pytest.fixture
def middleware_make_simple_server_mock(mocker):
    return mocker.patch.object(
        GraphQLMiddleware, "make_simple_server", new=mocker.Mock()
    )


@pytest.fixture
def type_defs():
    return """
        type Query {
            hello: String
        }
    """


@pytest.fixture
def resolvers():
    return {"Query": {"hello": lambda *_: "Hello"}}


def test_wsgi_simple_server_serve_forever_is_called(
    mocker, type_defs, resolvers, simple_server_mock
):
    mocker.patch("wsgiref.simple_server.make_server", return_value=simple_server_mock)
    start_simple_server(type_defs, resolvers)
    simple_server_mock.serve_forever.assert_called_once()


def test_keyboard_interrupt_is_handled_gracefully(mocker, type_defs, resolvers):
    mocker.patch(
        "wsgiref.simple_server.make_server", side_effect=KeyboardInterrupt("test")
    )
    start_simple_server(type_defs, resolvers)


def test_type_defs_resolvers_host_and_ip_are_passed_to_graphql_middleware(
    middleware_make_simple_server_mock, type_defs, resolvers
):
    start_simple_server(type_defs, resolvers, "0.0.0.0", 4444)
    middleware_make_simple_server_mock.assert_called_once_with(
        type_defs, resolvers, "0.0.0.0", 4444
    )


def test_default_host_and_ip_are_passed_to_graphql_middleware_if_not_set(
    middleware_make_simple_server_mock, type_defs, resolvers
):
    start_simple_server(type_defs, resolvers)
    middleware_make_simple_server_mock.assert_called_once_with(
        type_defs, resolvers, "127.0.0.1", 8888
    )


def test_default_host_and_ip_are_printed_on_server_creation(
    middleware_make_simple_server_mock, capsys
):  # pylint: disable=unused-argument
    start_simple_server("", {})
    captured = capsys.readouterr()
    assert "http://127.0.0.1:8888" in captured.out


def test_custom_host_and_ip_are_printed_on_server_creation(
    middleware_make_simple_server_mock, capsys
):  # pylint: disable=unused-argument
    start_simple_server("", {}, "0.0.0.0", 4444)
    captured = capsys.readouterr()
    assert "http://0.0.0.0:4444" in captured.out
