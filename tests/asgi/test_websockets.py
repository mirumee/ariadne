from ariadne.asgi import (
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_ACK,
    GQL_START,
    GQL_DATA,
    GQL_STOP,
    GQL_COMPLETE,
    GQL_CONNECTION_TERMINATE,
)


def test_ping_can_be_subscribed_using_websocket_connection(client):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP, "id": "test1"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "test1"
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_query_can_be_executed_using_websocket_connection(client):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test2",
                "payload": {"operationName": None, "query": "{ testRoot }",},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test2"
        assert response["payload"]["data"] == {"testRoot": None}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_immediate_disconnect(client):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_stop(client):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        ws.send_json({"type": GQL_STOP, "id": "test1"})
        response = ws.receive_json()
        assert response["type"] == GQL_COMPLETE
        assert response["id"] == "test1"
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
