import pytest

from ariadne import GraphQLMiddleware


@pytest.fixture
def make_server(mocker):
    return mocker.patch("wsgiref.simple_server.make_server", return_value=True)


def assert_make_server_called_once_with(
    make_server, base_class=GraphQLMiddleware, host="127.0.0.1", port=8888
):
    assert make_server.called
    assert make_server.call_count == 1

    called_with_args = make_server.call_args[0]
    assert len(called_with_args) == 3
    assert called_with_args[0] == host
    assert called_with_args[1] == port
    assert isinstance(called_with_args[2], base_class)


def test_make_simple_server_returns_mocked_true(type_defs, resolvers, make_server):
    result = GraphQLMiddleware.make_simple_server(type_defs, resolvers)
    assert_make_server_called_once_with(make_server, base_class=GraphQLMiddleware)
    assert result is True


def test_make_simple_server_creates_server_with_custom_host(
    type_defs, resolvers, make_server
):
    result = GraphQLMiddleware.make_simple_server(type_defs, resolvers, host="0.0.0.0")
    assert_make_server_called_once_with(
        make_server, base_class=GraphQLMiddleware, host="0.0.0.0"
    )
    assert result is True


def test_make_simple_server_creates_server_with_custom_port(
    type_defs, resolvers, make_server
):
    result = GraphQLMiddleware.make_simple_server(type_defs, resolvers, port=4444)
    assert_make_server_called_once_with(
        make_server, base_class=GraphQLMiddleware, port=4444
    )
    assert result is True


def test_make_simple_server_on_inheriting_type_respects_inheritance(
    type_defs, resolvers, make_server
):
    class CustomGraphQLMiddleware(GraphQLMiddleware):
        pass

    result = CustomGraphQLMiddleware.make_simple_server(type_defs, resolvers)
    assert_make_server_called_once_with(make_server, base_class=CustomGraphQLMiddleware)
    assert result is True
