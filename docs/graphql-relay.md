---
id: graphql-relay
title: GraphQL Relay
sidebar_label: GraphQL Relay
---

Since version **0.25**, Ariadne includes a `contrib` module that simplifies the process of creating a GraphQL server compatible with the [Relay specification](https://relay.dev/docs/guides/graphql-server-specification/).

## Minimal Example

Let's start with a minimal example using the following schema:

```graphql
interface Node {
  id: ID!
}

type Faction implements Node {
  id: ID!
  name: String
  ships(first: Int!, after: ID): ShipConnection
}

type Ship implements Node {
  id: ID!
  modelName: String
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
  node(id: ID!): Node
}
```

Ariadne provides built-in objects within `ariadne.contrib.relay` that help implement Relay features.

```python
from ariadne.contrib.relay import (
    RelayObjectType,
    RelayQueryType,
)

query = RelayQueryType()
ship = RelayObjectType("Ship")


@ship.node_resolver
async def resolve_ship(_, info, id: str):
    return ships_backend.get_by_id(id)


@query.node.type_resolver
def resolve_node_type(obj, *_):
    return obj["__typename"]
```

The `RelayObjectType` class includes a `node_resolver` decorator, which defines how instances of this type should be resolved when queried through `query.node`.

Additionally, `RelayQueryType` includes a `RelayNodeInterfaceType`, which functions like a standard Ariadne `InterfaceType` and requires a [`type_resolver`](/server/interfaces).

---

## Node Query

By default, `RelayQueryType` uses an ID decoder that **Base64 decodes the ID** and splits it by `:`. The first part of the decoded ID determines which node resolver to use.

For example, an ID of `U2hpcDox` decodes to `"Ship"` and `"1"`, meaning the `resolve_ship` method will be called with `"1"` as the `id` argument.

To customize this behavior, you can provide a custom ID decoder when instantiating `RelayQueryType`:

```python
def decode_global_id(kwargs) -> GlobalIDTuple:
    return GlobalIDTuple(*b64decode(kwargs["bid"]).decode().split(":"))


query = RelayQueryType(
    global_id_decoder=decode_global_id,
)
```

The above example assumes a **Node interface that uses `bid` instead of `id`**:

```graphql
interface Node {
  bid: ID!
}
```

---

## Connection Queries

Ariadne provides a `connection` decorator that simplifies handling connection-based queries. Consider the following example:

```python
from ariadne.contrib.relay import (
    ConnectionArguments,
    RelayConnection,
    RelayObjectType,
)

faction = RelayObjectType("Faction")

@faction.connection("ships")
async def resolve_ships(
    faction_obj,
    info,
    connection_arguments: ConnectionArguments,
    **kwargs,
):
    ships_slice = ships_backend.filter(id__gt=connection_arguments.after).first(connection_arguments.first)

    return RelayConnection(
        edges=ships_slice,
        total=ships_slice.count(),
        has_next_page=True if ships_slice.next_page else False,
        has_previous_page=True if ships_slice.previous_page else False,
    )
```

> The example above assumes the presence of a backend capable of retrieving data. Ariadne itself does **not** fetch or store data—this responsibility belongs to your application.

The `resolve_ships` resolver, decorated with `RelayObjectType.connection`, acts as a **Relay connection resolver**. It receives the standard `obj` and `info` arguments, along with `connection_arguments`, which contains pagination-related data. Additional data, if present, is accessible via `kwargs`.

This resolver must return a `RelayConnection` instance, with **pagination handled externally**—Ariadne does **not** implement pagination logic for you.

---

## Creating the Server

When creating an executable schema, ensure all **bindables** are included:

```python
from ariadne import make_executable_schema

app = GraphQL(
    make_executable_schema(schema, *query.bindables, faction, ship),
)
```
