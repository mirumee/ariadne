import pytest
from graphql import graphql_sync
from pytest_mock import MockFixture

from ariadne import make_executable_schema
from ariadne.contrib.relay.arguments import ConnectionArguments
from ariadne.contrib.relay.connection import RelayConnection
from ariadne.contrib.relay.objects import (
    RelayNodeInterfaceType,
    RelayObjectType,
    RelayQueryType,
    decode_global_id,
)
from ariadne.contrib.relay.types import (
    GlobalIDTuple,
)


@pytest.fixture
def friends_connection():
    return RelayConnection(
        edges=[{"id": "VXNlcjox", "name": "Alice"}, {"id": "VXNlcjoy", "name": "Bob"}],
        total=2,
        has_next_page=False,
        has_previous_page=False,
    )


def test_decode_global_id():
    assert decode_global_id({"id": "VXNlcjox"}) == GlobalIDTuple("User", "1")


def test_default_interface_decoder():
    node = RelayNodeInterfaceType()
    assert node.global_id_decoder is decode_global_id


def test_missing_node_resolver():
    with pytest.raises(ValueError):
        RelayNodeInterfaceType().get_node_resolver("NonExistingType")


def test_node_resolver_storage():
    def resolve_user(*_):
        pass

    node = RelayNodeInterfaceType()

    node.set_node_resolver("User", resolve_user)
    assert node.get_node_resolver("User") is resolve_user

    node.node_resolver("Post")(resolve_user)

    assert node.get_node_resolver("Post") is resolve_user


def test_query_type_node_field_resolver():
    # pylint: disable=protected-access,comparison-with-callable
    def resolve_node(*_):
        pass

    query = RelayQueryType(node_field_resolver=resolve_node)
    assert query._resolvers["node"] is resolve_node

    query = RelayQueryType()
    assert query._resolvers["node"] == query.default_resolve_node


def test_query_type_bindables():
    query = RelayQueryType()
    assert query.bindables == (query, query.node)


@pytest.mark.asyncio
async def test_query_type_default_resolve_node(mocker: MockFixture):
    query = RelayQueryType()
    mock_resolver = mocker.Mock()
    mock_info = mocker.Mock()
    query.node.node_resolver("User")(mock_resolver)
    assert (
        query.default_resolve_node(None, mock_info, id="VXNlcjox")
        == mock_resolver.return_value
    )
    mock_resolver.assert_called_once_with(None, mock_info, id="VXNlcjox")

    mock_async_resolver = mocker.AsyncMock()
    query.node.node_resolver("User")(mock_async_resolver)
    awaitable_resolver = query.default_resolve_node(None, mock_info, id="VXNlcjox")
    await awaitable_resolver
    mock_async_resolver.assert_awaited_once_with(None, mock_info, id="VXNlcjox")


def test_relay_object_type():
    object_type = RelayObjectType("User")
    assert object_type.connection_arguments_class == ConnectionArguments


def test_relay_object_resolve_wrapper(mocker: MockFixture, friends_connection):
    mock_resolver = mocker.Mock(return_value=friends_connection)
    mock_connection_arguments = mocker.Mock()
    mock_connection_arguments_class = mocker.Mock(
        return_value=mock_connection_arguments
    )

    object_type = RelayObjectType(
        "User", connection_arguments_class=mock_connection_arguments_class
    )
    wrapped_resolver = object_type.resolve_wrapper(mock_resolver)

    result = wrapped_resolver(None, None, first=10)
    assert result == {
        "edges": [
            {"node": {"id": "VXNlcjox", "name": "Alice"}, "cursor": "VXNlcjox"},
            {"node": {"id": "VXNlcjoy", "name": "Bob"}, "cursor": "VXNlcjoy"},
        ],
        "pageInfo": {
            "hasNextPage": False,
            "hasPreviousPage": False,
            "startCursor": "VXNlcjox",
            "endCursor": "VXNlcjoy",
        },
    }

    mock_resolver.assert_called_once_with(
        None, None, mock_connection_arguments, first=10
    )


@pytest.mark.asyncio
async def test_relay_object_resolve_wrapper_async(
    mocker: MockFixture, friends_connection
):
    mock_resolver = mocker.AsyncMock(return_value=friends_connection)

    object_type = RelayObjectType("User")
    wrapped_resolver = object_type.resolve_wrapper(mock_resolver)

    result = await wrapped_resolver(None, None, first=10)
    assert result == {
        "edges": [
            {"node": {"id": "VXNlcjox", "name": "Alice"}, "cursor": "VXNlcjox"},
            {"node": {"id": "VXNlcjoy", "name": "Bob"}, "cursor": "VXNlcjoy"},
        ],
        "pageInfo": {
            "hasNextPage": False,
            "hasPreviousPage": False,
            "startCursor": "VXNlcjox",
            "endCursor": "VXNlcjoy",
        },
    }


def test_relay_object_resolve_wrapper_with_custom_arguments():
    pass


def test_relay_object_connection_decorator(mocker: MockFixture):
    # pylint: disable=protected-access
    object_type = RelayObjectType("User")
    mock_resolve_wrapper = mocker.patch.object(object_type, "resolve_wrapper")

    @object_type.connection("friends")
    def resolve_friends(*_):
        pass

    mock_resolve_wrapper.assert_called_once_with(resolve_friends)

    assert object_type._resolvers["friends"] == mock_resolve_wrapper.return_value


def test_relay_query(
    relay_type_defs,
    relay_query,
):
    schema = make_executable_schema(
        relay_type_defs,
        *relay_query.bindables,
    )
    result = graphql_sync(schema, "{ rebels { bid name } }")

    assert result.errors is None
    assert result.data == {
        "rebels": {"bid": "RmFjdGlvbjox", "name": "Alliance to Restore the Republic"}
    }


def test_relay_node_query_ship(
    relay_type_defs,
    relay_query_with_node_resolvers,
):
    schema = make_executable_schema(
        relay_type_defs,
        *relay_query_with_node_resolvers.bindables,
    )
    result = graphql_sync(
        schema, '{ node(bid: "U2hpcDoz") { ... on Ship { bid name } } }'
    )

    assert result.errors is None
    assert result.data == {"node": {"bid": "U2hpcDoz", "name": "A-Wing"}}


def test_relay_node_query_faction(
    relay_type_defs,
    relay_query_with_node_resolvers,
):
    schema = make_executable_schema(
        relay_type_defs,
        *relay_query_with_node_resolvers.bindables,
    )
    result = graphql_sync(
        schema, '{ node(bid: "RmFjdGlvbjoy") { ... on Faction { bid name } } }'
    )

    assert result.errors is None
    assert result.data == {"node": {"bid": "RmFjdGlvbjoy", "name": "Galactic Empire"}}
