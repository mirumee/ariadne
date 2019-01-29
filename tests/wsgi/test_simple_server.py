import pytest

from ariadne import make_executable_schema, start_simple_server
from ariadne.wsgi import GraphQL


@pytest.fixture
def make_server(mocker):
    return mocker.patch("wsgiref.simple_server.make_server")


def test_start_simple_server_returns_mocked_true(
    type_defs, resolvers, make_server
):  # pylint: disable=unused-argument
    schema = make_executable_schema(type_defs, resolvers)
    start_simple_server(schema)
    assert make_server.call_count == 1


def test_start_simple_server_creates_server_with_custom_host(
    type_defs, resolvers, make_server
):
    schema = make_executable_schema(type_defs, resolvers)
    start_simple_server(schema, host="0.0.0.0")
    called_with_args = make_server.call_args[0]
    assert called_with_args[0] == "0.0.0.0"


def test_start_simple_server_creates_server_with_custom_port(
    type_defs, resolvers, make_server
):
    schema = make_executable_schema(type_defs, resolvers)
    start_simple_server(schema, port=4444)
    called_with_args = make_server.call_args[0]
    assert called_with_args[1] == 4444


def test_start_simple_server_from_inheriting_type_respects_inheritance(
    type_defs, resolvers, make_server
):
    class CustomGraphQL(GraphQL):
        pass

    schema = make_executable_schema(type_defs, resolvers)
    start_simple_server(schema, server_class=CustomGraphQL)
    make_server.assert_called_once()
    called_with_args = make_server.call_args[0]
    assert isinstance(called_with_args[2], CustomGraphQL)
