# pylint: disable=not-context-manager
from unittest.mock import ANY, Mock

from starlette.testclient import TestClient

from ariadne.asgi import (
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_DATA,
    GQL_ERROR,
    GQL_START,
    GraphQL,
)


def test_custom_context_value_is_passed_to_resolvers(schema):
    app = GraphQL(schema, context_value={"test": "TEST-CONTEXT"})
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testContext }"})
    assert response.json() == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_context_value_function_is_set_and_called_by_app(schema):
    get_context_value = Mock(return_value=True)
    app = GraphQL(schema, context_value=get_context_value)
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_context_value.assert_called_once()


def test_custom_context_value_function_result_is_passed_to_resolvers(schema):
    get_context_value = Mock(return_value={"test": "TEST-CONTEXT"})
    app = GraphQL(schema, context_value=get_context_value)
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testContext }"})
    assert response.json() == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_root_value_is_passed_to_query_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testRoot }"})
    assert response.json() == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_is_passed_to_subscription_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    client = TestClient(app)
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { testRoot }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["payload"] == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_function_is_called_by_query(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_root_value.assert_called_once()


def test_custom_root_value_function_is_called_by_subscription(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    client = TestClient(app)
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
        get_root_value.assert_called_once()


def test_custom_root_value_function_is_called_with_context_value(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(
        schema, context_value={"test": "TEST-CONTEXT"}, root_value=get_root_value
    )
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_root_value.assert_called_once_with({"test": "TEST-CONTEXT"}, ANY)


def execute_failing_query(app):
    client = TestClient(app)
    client.post("/", json={"query": "{ error }"})


def test_custom_logger_is_used_to_log_query_error(schema):
    logger = Mock(error=Mock(return_value=True))
    app = GraphQL(schema, logger=logger)
    execute_failing_query(app)
    logger.error.assert_called_once()


def test_custom_logger_is_used_to_log_subscription_source_error(schema):
    logger = Mock(error=Mock(return_value=True))
    app = GraphQL(schema, logger=logger)
    client = TestClient(app)
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { sourceError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        logger.error.assert_called_once()


def test_custom_logger_is_used_to_log_subscription_resolver_error(schema):
    logger = Mock(error=Mock(return_value=True))
    app = GraphQL(schema, logger=logger)
    client = TestClient(app)
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { resolverError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        logger.error.assert_called_once()


def test_custom_error_formatter_is_used_to_format_query_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    execute_failing_query(app)
    error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_syntax_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    client = TestClient(app)
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {"type": GQL_START, "id": "test1", "payload": {"query": "subscription {"}}
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_ERROR
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_source_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    client = TestClient(app)
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { sourceError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_resolver_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    client = TestClient(app)
    with client.websocket_connect("/", "graphql-ws") as ws:
        ws.send_json({"type": GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { resolverError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GQL_DATA
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_error_formatter_is_called_with_debug_enabled(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, debug=True, error_formatter=error_formatter)
    execute_failing_query(app)
    error_formatter.assert_called_once_with(ANY, True)


def test_error_formatter_is_called_with_debug_disabled(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, debug=False, error_formatter=error_formatter)
    execute_failing_query(app)
    error_formatter.assert_called_once_with(ANY, False)
