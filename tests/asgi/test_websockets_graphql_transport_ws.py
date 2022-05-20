# pylint: disable=not-context-manager
import pytest
from graphql import parse
from graphql.language import OperationType
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler
from ariadne.types import WebSocketConnectionError
from ariadne.utils import get_operation_type


def test_field_can_be_subscribed_using_websocket_connection_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"


def test_field_can_be_subscribed_using_unnamed_operation_in_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": None,
                    "query": "subscription { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"


def test_field_can_be_subscribed_using_named_operation_in_websocket_connection_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "PingTest",
                    "query": "subscription PingTest { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert response["id"] == "test1"


def test_query_can_be_executed_using_websocket_connection_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test2",
                "payload": {
                    "operationName": None,
                    "query": "query Hello($name: String){ hello(name: $name) }",
                    "variables": {"name": "John"},
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test2"
        assert response["payload"]["data"] == {"hello": "Hello, John!"}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert response["id"] == "test2"


def test_immediate_disconnect_on_invalid_type_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": "INVALID_TYPE"})
        with pytest.raises(WebSocketDisconnect):
            assert ws.receive_json()


def test_complete_graphql_transport_ws(client_graphql_transport_ws):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_COMPLETE, "id": "test1"})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"


def test_pong_graphql_transport_ws(client_graphql_transport_ws):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_PONG,
            }
        )


def test_custom_websocket_on_connect_is_called_graphql_transport_ws(schema):
    test_payload = None

    def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    websocket_handler = GraphQLTransportWSHandler(on_connect=on_connect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload


def test_custom_websocket_on_connect_is_called_with_payload_graph_graphql_transport_ws(
    schema,
):
    test_payload = {"test": "ok"}

    def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    websocket_handler = GraphQLTransportWSHandler(on_connect=on_connect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT,
                "payload": test_payload,
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload


def test_custom_websocket_on_connect_is_awaited_if_its_async_graphql_transport_ws(
    schema,
):
    test_payload = {"test": "ok"}

    async def on_connect(websocket, payload):
        assert payload == test_payload
        websocket.scope["payload"] = payload

    websocket_handler = GraphQLTransportWSHandler(on_connect=on_connect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT,
                "payload": test_payload,
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        assert ws.scope["payload"] == test_payload


def test_error_in_custom_websocket_on_connect_closes_connection_graphql_transport_ws(
    schema,
):
    def on_connect(websocket, payload):
        raise ValueError("Oh No!")

    websocket_handler = GraphQLTransportWSHandler(on_connect=on_connect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_custom_websocket_connection_error_closes_connection_graphql_transport_ws(
    schema,
):
    def on_connect(websocket, payload):
        raise WebSocketConnectionError({"msg": "Token required", "code": "auth_error"})

    websocket_handler = GraphQLTransportWSHandler(on_connect=on_connect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_custom_websocket_on_operation_is_called_graphql_transport_ws(schema):
    def on_operation(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_operation"] = True

    websocket_handler = GraphQLTransportWSHandler(on_operation=on_operation)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}

        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE
        assert ws.scope["on_operation"] is True


def test_custom_websocket_on_operation_is_awaited_if_its_async_graphql_transport_ws(
    schema,
):
    async def on_operation(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_operation"] = True

    websocket_handler = GraphQLTransportWSHandler(on_operation=on_operation)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_COMPLETE, "id": "test1"})
        assert ws.scope["on_operation"] is True


def test_error_in_custom_websocket_on_operation_is_handled_graphql_transport_ws(schema):
    async def on_operation(websocket, operation):
        raise ValueError("Oh No!")

    websocket_handler = GraphQLTransportWSHandler(on_operation=on_operation)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}


def test_custom_websocket_on_complete_is_called_on_disconnect_graphql_transport_ws(
    schema,
):
    def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    websocket_handler = GraphQLTransportWSHandler(on_complete=on_complete)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )

    assert ws.scope["on_complete"] is True


def test_custom_websocket_on_complete_is_called_on_operation_complete_grapqhl_transport_ws(
    schema,
):
    def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    websocket_handler = GraphQLTransportWSHandler(on_complete=on_complete)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}

        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE

        assert ws.scope["on_complete"] is True


def test_custom_websocket_on_complete_is_awaited_if_its_async_graphql_transport_ws(
    schema,
):
    async def on_complete(websocket, operation):
        assert operation.name == "TestOp"
        websocket.scope["on_complete"] = True

    websocket_handler = GraphQLTransportWSHandler(on_complete=on_complete)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE

    assert ws.scope["on_complete"] is True


def test_error_in_custom_websocket_on_complete_is_handled_graphql_transport_ws(schema):
    async def on_complete(websocket, operation):
        raise ValueError("Oh No!")

    websocket_handler = GraphQLTransportWSHandler(on_complete=on_complete)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {
                    "operationName": "TestOp",
                    "query": "subscription TestOp { ping }",
                },
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        assert response["payload"]["data"] == {"ping": "pong"}
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_COMPLETE


def test_custom_websocket_on_disconnect_is_called_on_invalid_operation_graphql_transport_ws(
    schema,
):
    def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    websocket_handler = GraphQLTransportWSHandler(on_disconnect=on_disconnect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": "INVALID"})
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_custom_websocket_on_disconnect_is_called_on_connection_close_graphql_transport_ws(
    schema,
):
    def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    websocket_handler = GraphQLTransportWSHandler(on_disconnect=on_disconnect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_custom_websocket_on_disconnect_is_awaited_if_its_async_graphql_transport_ws(
    schema,
):
    async def on_disconnect(websocket):
        websocket.scope["on_disconnect"] = True

    websocket_handler = GraphQLTransportWSHandler(on_disconnect=on_disconnect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": "INVALID"})
        assert "on_disconnect" not in ws.scope

    assert ws.scope["on_disconnect"] is True


def test_error_in_custom_websocket_on_disconnect_is_handled_graphql_transport_ws(
    schema,
):
    async def on_disconnect(websocket):
        raise ValueError("Oh No!")

    websocket_handler = GraphQLTransportWSHandler(on_disconnect=on_disconnect)
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": "INVALID"})


def test_too_many_connection_init_messages_graphql_transport_ws(
    schema,
):
    handler = GraphQLTransportWSHandler()
    app = GraphQL(schema, websocket_handler=handler)
    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        with pytest.raises(WebSocketDisconnect, match="4429"):
            ws.receive_json()


def test_get_operation_type():
    graphql_document = parse("subscription ping {ping} query other { dummy }")
    operation_type = get_operation_type(graphql_document, "ping")
    assert operation_type == OperationType.SUBSCRIPTION

    operation_type = get_operation_type(graphql_document, "other")
    assert operation_type == OperationType.QUERY

    operation_type = get_operation_type(graphql_document)
    assert operation_type == OperationType.SUBSCRIPTION


def test_connection_not_acknowledged_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        with pytest.raises(WebSocketDisconnect, match="4401"):
            ws.receive_json()


def test_duplicate_operation_id_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        ws.receive_json()
        with pytest.raises(WebSocketDisconnect, match="4409"):
            ws.receive_json()


def test_invalid_operation_id_is_handled_graphql_transport_ws(
    client_graphql_transport_ws,
):
    with client_graphql_transport_ws.websocket_connect(
        "/", ["graphql-transport-ws"]
    ) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_COMPLETE, "id": "test1"})
        ws.receive_json()


def test_schema_not_set_graphql_transport_ws(
    client_graphql_transport_ws,
):

    client_graphql_transport_ws.app.websocket_handler.schema = None
    with pytest.raises(TypeError):
        with client_graphql_transport_ws.websocket_connect(
            "/", ["graphql-transport-ws"]
        ) as ws:
            ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
            ws.send_json(
                {
                    "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                    "id": "test1",
                    "payload": {"query": "subscription { ping }"},
                }
            )


def test_http_handler_not_set_graphql_transport_ws(
    client_graphql_transport_ws,
):

    client_graphql_transport_ws.app.websocket_handler.http_handler = None
    with pytest.raises(TypeError):
        with client_graphql_transport_ws.websocket_connect(
            "/", ["graphql-transport-ws"]
        ) as ws:
            ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
            ws.send_json(
                {
                    "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                    "id": "test2",
                    "payload": {
                        "operationName": None,
                        "query": "query Hello($name: String){ hello(name: $name) }",
                        "variables": {"name": "John"},
                    },
                }
            )
