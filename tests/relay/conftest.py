from base64 import b64decode

import pytest

from ariadne.contrib.relay import (
    ConnectionArguments,
    GlobalIDTuple,
    RelayConnection,
    RelayNodeInterfaceType,
    RelayObjectType,
    RelayQueryType,
)


@pytest.fixture
def relay_type_defs():
    return """\
interface Node {
  bid: ID!
}

type Faction implements Node {
  bid: ID!
  name: String
  ships(first: Int!, after: ID): ShipConnection
}

type Ship implements Node {
  bid: ID!
  name: String
}

type ShipConnection {
  edges: [ShipEdge]
  pageInfo: PageInfo!
  ships: [Ship]
  totalCount: Int
}

type ShipEdge {
  cursor: String!
  node: Ship
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  rebels: Faction
  empire: Faction
  node(bid: ID!): Node
}
"""


@pytest.fixture
def global_id_decoder():
    return lambda gid: GlobalIDTuple(*b64decode(gid).decode().split(":"))


@pytest.fixture
def relay_node_interface():
    return RelayNodeInterfaceType()


@pytest.fixture
def relay_query(factions, relay_node_interface, global_id_decoder):
    query = RelayQueryType(
        node=relay_node_interface,
        global_id_decoder=global_id_decoder,
        id_field="bid",
    )
    query.set_field("rebels", lambda *_: factions[0])
    query.set_field("empire", lambda *_: factions[1])
    query.node.set_field("bid", lambda obj, *_: obj["id"])
    return query


@pytest.fixture
def ships():
    return [
        {
            "id": "U2hpcDox",
            "name": "X-Wing",
            "factionId": "RmFjdGlvbjox",
        },
        {
            "id": "U2hpcDoy",
            "name": "Y-Wing",
            "factionId": "RmFjdGlvbjox",
        },
        {
            "id": "U2hpcDoz",
            "name": "A-Wing",
            "factionId": "RmFjdGlvbjox",
        },
        {
            "id": "U2hpcDo0",
            "name": "Millennium Falcon",
            "factionId": "RmFjdGlvbjox",
        },
        {
            "id": "U2hpcDo1",
            "name": "Home One",
            "factionId": "RmFjdGlvbjox",
        },
        {
            "id": "U2hpcDo2",
            "name": "TIE Fighter",
            "factionId": "RmFjdGlvbjoy",
        },
        {
            "id": "U2hpcDo3",
            "name": "TIE Bomber",
            "factionId": "RmFjdGlvbjoy",
        },
        {
            "id": "U2hpcDo4",
            "name": "TIE Interceptor",
            "factionId": "RmFjdGlvbjoy",
        },
        {
            "id": "U2hpcDo5",
            "name": "Darth Vader's TIE Advanced",
            "factionId": "RmFjdGlvbjoy",
        },
    ]


@pytest.fixture
def factions():
    return [
        {
            "id": "RmFjdGlvbjox",
            "name": "Alliance to Restore the Republic",
        },
        {"id": "RmFjdGlvbjoy", "name": "Galactic Empire"},
    ]


@pytest.fixture
def relay_faction_object(factions):
    faction = RelayObjectType("Faction")
    faction.node_resolver(
        lambda *_, bid: [
            {"__typename": "Faction", **faction}
            for faction in factions
            if faction["id"] == bid
        ][0]
    )
    return faction


@pytest.fixture
def relay_ship_object(ships):
    ship = RelayObjectType("Ship")
    ship.node_resolver(
        lambda *_, bid: [
            {"__typename": "Ship", **ship} for ship in ships if ship["id"] == bid
        ][0]
    )
    return ship


@pytest.fixture
def ship_slice_resolver(ships):
    def resolver(
        faction_obj, info, connection_arguments: ConnectionArguments, **kwargs
    ):
        faction_ships = [
            ship for ship in ships if ship["factionId"] == faction_obj["id"]
        ]
        total = len(faction_ships)
        if connection_arguments.after:
            after_index = (
                faction_ships.index(
                    next(
                        ship
                        for ship in faction_ships
                        if ship["id"] == connection_arguments.after
                    )
                )
                + 1
            )
        else:
            after_index = 0
        ships_slice = faction_ships[
            after_index : after_index + connection_arguments.first
        ]

        return RelayConnection(
            edges=ships_slice,
            total=total,
            has_next_page=after_index + connection_arguments.first < total,
            has_previous_page=after_index > 0,
        )

    return resolver
