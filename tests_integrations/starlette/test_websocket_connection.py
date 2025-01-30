from starlette.applications import Starlette
from starlette.routing import Mount, WebSocketRoute
from starlette.testclient import TestClient

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler

subscription_type = SubscriptionType()


@subscription_type.source("counter")
async def counter_source(*_):
    yield 1


@subscription_type.field("counter")
async def counter_resolve(obj, *_):
    return obj


schema = make_executable_schema(
    """
    type Query {
        _unused: String
    }

    type Subscription {
        counter: Int!
    }
    """,
    subscription_type,
)


graphql = GraphQL(
    schema,
    websocket_handler=GraphQLTransportWSHandler(),
)

app = Starlette(
    routes=[
        WebSocketRoute("/graphql", graphql.handle_websocket),
        Mount("/mounted", graphql),
    ],
)

client = TestClient(app)


def test_run_graphql_subscription_through_route():
    with client.websocket_connect("/graphql", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test2",
                "payload": {
                    "operationName": None,
                    "query": "subscription { counter }",
                    "variables": None,
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test2"
        assert response["payload"]["data"] == {"counter": 1}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert response["id"] == "test2"


def test_run_graphql_subscription_through_mount():
    with client.websocket_connect("/mounted/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test2",
                "payload": {
                    "operationName": None,
                    "query": "subscription { counter }",
                    "variables": None,
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test2"
        assert response["payload"]["data"] == {"counter": 1}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert response["id"] == "test2"
