# pylint: disable=not-context-manager

from starlette.testclient import TestClient

from ariadne.asgi import (
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_ERROR,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_TERMINATE,
    GQL_START,
    GQL_DATA,
    GQL_STOP,
    GQL_COMPLETE,
    GraphQL,
    WebSocketConnectionError,
)


def test_field_can_be_subscribed_using_websocket_connection(client):
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


def test_field_can_be_subscribed_using_unnamed_operation_in_websocket_connection(
    client,
):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": None,
                    "query": "subscription { ping }",
                },
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


def test_field_can_be_subscribed_using_named_operation_in_websocket_connection(client):
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "PingTest",
                    "query": "subscription PingTest { ping }",
                },
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


def test_custom_websocket_on_connect_is_called(schema):
    test_payload = None

    def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    app = GraphQL(schema, on_connect=on_connect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_connect_is_called_with_payload(schema):
    test_payload = {"test": "ok"}

    def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    app = GraphQL(schema, on_connect=on_connect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT, "payload": test_payload})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_connect_is_awaited_if_its_async(schema):
    test_payload = {"test": "ok"}

    async def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    app = GraphQL(schema, on_connect=on_connect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT, "payload": test_payload})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_error_in_custom_websocket_on_connect_is_handled(schema):
    def on_connect(websocket, payload):
        raise ValueError("Oh No!")

    app = GraphQL(schema, on_connect=on_connect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ERROR
        assert response["payload"] == {"message": "Unexpected error has occurred."}


def test_custom_websocket_connection_error_in_custom_websocket_on_connect_is_handled(
    schema,
):
    def on_connect(websocket, payload):
        raise WebSocketConnectionError({"msg": "Token required", "code": "auth_error"})

    app = GraphQL(schema, on_connect=on_connect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ERROR
        assert response["payload"] == {"msg": "Token required", "code": "auth_error"}


def test_custom_websocket_on_operation_is_called(schema):
    def on_operation(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_operation"] = True

    app = GraphQL(schema, on_operation=on_operation)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP})
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "ping"}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
        assert ws.scope["on_operation"] is True


def test_custom_websocket_on_operation_is_awaited_if_its_async(schema):
    async def on_operation(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_operation"] = True

    app = GraphQL(schema, on_operation=on_operation)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP})
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "ping"}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
        assert ws.scope["on_operation"] is True


def test_error_in_custom_websocket_on_operation_is_handled(schema):
    async def on_operation(websocket, operation):
        raise ValueError("Oh No!")

    app = GraphQL(schema, on_operation=on_operation)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP})
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "ping"}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_complete_is_called(schema):
    def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    app = GraphQL(schema, on_complete=on_complete)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP})
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "ping"}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
        assert "on_complete" not in ws.scope

    assert ws.scope["on_complete"] is True


def test_custom_websocket_on_complete_is_awaited_if_its_async(schema):
    async def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    app = GraphQL(schema, on_complete=on_complete)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP})
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "ping"}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
        assert "on_complete" not in ws.scope

    assert ws.scope["on_complete"] is True


def test_error_in_custom_websocket_on_complete_is_handled(schema):
    async def on_complete(websocket, operation):
        raise ValueError("Oh No!")

    app = GraphQL(schema, on_complete=on_complete)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GQL_STOP})
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "ping"}
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})


def test_custom_websocket_on_disconnect_is_called_on_terminate_message(schema):
    def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    app = GraphQL(schema, on_disconnect=on_disconnect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_custom_websocket_on_disconnect_is_called_on_connection_close(schema):
    def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    app = GraphQL(schema, on_disconnect=on_disconnect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_custom_websocket_on_disconnect_is_awaited_if_its_async(schema):
    async def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    app = GraphQL(schema, on_disconnect=on_disconnect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_error_in_custom_websocket_on_disconnect_is_handled(schema):
    async def on_disconnect(websocket):
        raise ValueError("Oh No!")

    app = GraphQL(schema, on_disconnect=on_disconnect)
    client = TestClient(app)

    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        ws.send_json({"type": GQL_CONNECTION_TERMINATE})
