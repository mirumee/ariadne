import pytest

from ariadne import GraphQLMiddleware


@pytest.fixture
def make_server(mocker):
    return mocker.patch("wsgiref.simple_server.make_server", return_value=True)


def test_make_simple_server_returns_mocked_true(
    type_defs, resolvers, make_server
):  # pylint: disable=unused-argument
    result = GraphQLMiddleware.make_simple_server(type_defs, resolvers)
    assert result is True


def test_make_simple_server_creates_server_with_custom_host(
    type_defs, resolvers, make_server
):
    GraphQLMiddleware.make_simple_server(type_defs, resolvers, host="0.0.0.0")
    assert make_server.call_count == 1
    called_with_args = make_server.call_args[0]
    assert called_with_args[0] == "0.0.0.0"


def test_make_simple_server_creates_server_with_custom_port(
    type_defs, resolvers, make_server
):
    GraphQLMiddleware.make_simple_server(type_defs, resolvers, port=4444)
    assert make_server.call_count == 1
    called_with_args = make_server.call_args[0]
    assert called_with_args[1] == 4444


def test_make_simple_server_from_inheriting_type_respects_inheritance(
    type_defs, resolvers, make_server
):
    class CustomGraphQLMiddleware(GraphQLMiddleware):
        pass

    CustomGraphQLMiddleware.make_simple_server(type_defs, resolvers)
    assert make_server.call_count == 1
    called_with_args = make_server.call_args[0]
    assert isinstance(called_with_args[2], CustomGraphQLMiddleware)
