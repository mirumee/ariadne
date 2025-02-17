import pytest
from graphql import extend_schema, graphql_sync, parse
from pytest_mock import MockFixture

from ariadne import make_executable_schema
from ariadne.contrib.relay.arguments import (
    ConnectionArguments,
    ForwardConnectionArguments,
)
from ariadne.contrib.relay.connection import RelayConnection
from ariadne.contrib.relay.objects import (
    RelayObjectType,
    RelayQueryType,
    decode_global_id,
)


@pytest.fixture
def friends_connection():
    edges = [{"id": "VXNlcjox", "name": "Alice"}, {"id": "VXNlcjoy", "name": "Bob"}]
    return RelayConnection(
        edges=edges,
        total=len(edges),
        has_next_page=False,
        has_previous_page=False,
    )


def test_default_id_decoder():
    query = RelayQueryType()
    assert query.global_id_decoder is decode_global_id


def test_missing_node_resolver(relay_type_defs, relay_query):
    schema = make_executable_schema(relay_type_defs, *relay_query.bindables)
    with pytest.raises(ValueError):
        relay_query.get_node_resolver("NonExistingType", schema)


def test_node_resolver_storage(relay_type_defs, relay_query: RelayQueryType):
    ship = RelayObjectType("Ship")

    def resolve_ship(*_):
        pass

    ship.node_resolver(resolve_ship)

    schema = make_executable_schema(relay_type_defs, *relay_query.bindables, ship)

    assert relay_query.get_node_resolver("Ship", schema) is resolve_ship

    # extended schema re-creates the graphql object types
    extended_schema = extend_schema(
        schema, parse("extend type Query { fleet: [Ship] }")
    )

    assert relay_query.get_node_resolver("Ship", extended_schema) is resolve_ship


def test_query_type_node_field_resolver():
    query = RelayQueryType()
    assert query._resolvers["node"] == query.resolve_node


def test_query_type_bindables():
    query = RelayQueryType()
    assert query.bindables == (query, query.node)


def test_query_type_default_resolve_node(mocker: MockFixture, relay_type_defs):
    query = RelayQueryType()
    mock_resolver = mocker.Mock()
    ship = RelayObjectType("Ship")
    ship.node_resolver(mock_resolver)
    schema = make_executable_schema(relay_type_defs, query, ship)
    mock_info = mocker.Mock(schema=schema)

    assert (
        query.resolve_node(None, mock_info, id="U2hpcDox") == mock_resolver.return_value
    )
    mock_resolver.assert_called_once_with(None, mock_info, id="U2hpcDox")


@pytest.mark.asyncio
async def test_query_type_default_async_resolve_node(
    mocker: MockFixture, relay_type_defs
):
    query = RelayQueryType()
    ship = RelayObjectType("Ship")
    mock_async_resolver = mocker.AsyncMock()
    ship.node_resolver(mock_async_resolver)
    schema = make_executable_schema(relay_type_defs, query, ship)
    mock_info = mocker.Mock(schema=schema)

    awaitable_resolver = query.resolve_node(None, mock_info, id="U2hpcDox")
    await awaitable_resolver
    mock_async_resolver.assert_awaited_once_with(None, mock_info, id="U2hpcDox")


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
        "totalCount": 2,
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
    mock_connection_arguments_class.assert_called_once_with(first=10)


@pytest.mark.asyncio
async def test_relay_object_resolve_wrapper_async(friends_connection):
    async def resolver(*_, **__):
        return friends_connection

    object_type = RelayObjectType("User")
    wrapped_resolver = object_type.resolve_wrapper(resolver)

    result = await wrapped_resolver(None, None, first=10)
    assert result == {
        "totalCount": 2,
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


def test_relay_object_resolve_wrapper_without_edges(
    mocker: MockFixture, friends_connection
):
    edges = []
    friends_connection.edges = edges
    friends_connection.total = len(edges)
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
        "totalCount": 0,
        "edges": [],
        "pageInfo": {
            "hasNextPage": False,
            "hasPreviousPage": False,
            "startCursor": None,
            "endCursor": None,
        },
    }

    mock_resolver.assert_called_once_with(
        None, None, mock_connection_arguments, first=10
    )
    mock_connection_arguments_class.assert_called_once_with(first=10)


def test_relay_object_resolve_wrapper_with_custom_arguments(mocker: MockFixture):
    object_type = RelayObjectType(
        "User", connection_arguments_class=ForwardConnectionArguments
    )
    mock_resolver = mocker.Mock()

    wrapped_resolver = object_type.resolve_wrapper(mock_resolver)
    wrapped_resolver(None, None, first=10, after="VXNlcjox")

    connection_arg_call = mock_resolver.call_args_list[0].args[2]

    assert connection_arg_call.first == 10
    assert connection_arg_call.after == "VXNlcjox"


def test_relay_object_connection_decorator(mocker: MockFixture):
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
    relay_query,
    relay_ship_object,
):
    schema = make_executable_schema(
        relay_type_defs,
        *relay_query.bindables,
        relay_ship_object,
    )
    result = graphql_sync(
        schema, '{ node(bid: "U2hpcDoz") { ... on Ship { bid name } } }'
    )

    assert result.errors is None
    assert result.data == {"node": {"bid": "U2hpcDoz", "name": "A-Wing"}}


def test_relay_node_query_faction(
    relay_type_defs,
    relay_query,
    relay_faction_object,
):
    schema = make_executable_schema(
        relay_type_defs,
        *relay_query.bindables,
        relay_faction_object,
    )
    result = graphql_sync(
        schema, '{ node(bid: "RmFjdGlvbjoy") { ... on Faction { bid name } } }'
    )

    assert result.errors is None
    assert result.data == {"node": {"bid": "RmFjdGlvbjoy", "name": "Galactic Empire"}}
