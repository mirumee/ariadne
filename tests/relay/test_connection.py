from graphql import graphql_sync

from ariadne import make_executable_schema
from ariadne.contrib.relay import RelayConnection, RelayObjectType


def test_relay_connection():
    connection = RelayConnection(
        edges=[{"id": "VXNlcjox", "name": "Alice"}, {"id": "VXNlcjoy", "name": "Bob"}],
        total=2,
        has_next_page=False,
        has_previous_page=False,
    )
    assert connection.total == 2
    assert connection.has_next_page is False
    assert connection.has_previous_page is False
    assert connection.get_cursor({"id": "VXNlcjox"}) == "VXNlcjox"
    assert connection.get_page_info({}) == {
        "hasNextPage": False,
        "hasPreviousPage": False,
        "startCursor": "VXNlcjox",
        "endCursor": "VXNlcjoy",
    }
    assert connection.get_edges() == [
        {"node": {"id": "VXNlcjox", "name": "Alice"}, "cursor": "VXNlcjox"},
        {"node": {"id": "VXNlcjoy", "name": "Bob"}, "cursor": "VXNlcjoy"},
    ]


CONNECTION_QUERY = """\
query GetShips {
  rebels{
    bid
    name
    ships(first: 6) {
      ...ShipConnectionFragment
    }
    moreShips: ships(first: 2, after: "U2hpcDoy") {
      ...ShipConnectionFragment
    }
  }
}


fragment ShipConnectionFragment on ShipConnection {
  pageInfo {
    hasNextPage
    hasPreviousPage
    startCursor
    endCursor
  }
  edges {
    cursor
    node {
      bid
      name
    }
  }
}
"""


def test_relay_query_with_connection(relay_type_defs, relay_query, ship_slice_resolver):
    faction = RelayObjectType("Faction")

    faction.connection("ships")(ship_slice_resolver)

    schema = make_executable_schema(
        relay_type_defs,
        *relay_query.bindables,
        faction,
    )
    result = graphql_sync(schema, CONNECTION_QUERY)

    assert result.errors is None
    assert result.data == {
        "rebels": {
            "bid": "RmFjdGlvbjox",
            "name": "Alliance to Restore the Republic",
            "ships": {
                "pageInfo": {
                    "hasNextPage": False,
                    "hasPreviousPage": False,
                    "startCursor": "U2hpcDox",
                    "endCursor": "U2hpcDo1",
                },
                "edges": [
                    {
                        "cursor": "U2hpcDox",
                        "node": {"bid": "U2hpcDox", "name": "X-Wing"},
                    },
                    {
                        "cursor": "U2hpcDoy",
                        "node": {"bid": "U2hpcDoy", "name": "Y-Wing"},
                    },
                    {
                        "cursor": "U2hpcDoz",
                        "node": {"bid": "U2hpcDoz", "name": "A-Wing"},
                    },
                    {
                        "cursor": "U2hpcDo0",
                        "node": {"bid": "U2hpcDo0", "name": "Millennium Falcon"},
                    },
                    {
                        "cursor": "U2hpcDo1",
                        "node": {"bid": "U2hpcDo1", "name": "Home One"},
                    },
                ],
            },
            "moreShips": {
                "pageInfo": {
                    "hasNextPage": True,
                    "hasPreviousPage": True,
                    "startCursor": "U2hpcDoz",
                    "endCursor": "U2hpcDo0",
                },
                "edges": [
                    {
                        "cursor": "U2hpcDoz",
                        "node": {"bid": "U2hpcDoz", "name": "A-Wing"},
                    },
                    {
                        "cursor": "U2hpcDo0",
                        "node": {"bid": "U2hpcDo0", "name": "Millennium Falcon"},
                    },
                ],
            },
        }
    }
