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
from ariadne.types import Extension


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


def test_async_context_value_function_result_is_awaited_before_passing_to_resolvers(
    schema,
):
    async def get_context_value(*_):
        return {"test": "TEST-ASYNC-CONTEXT"}

    app = GraphQL(schema, context_value=get_context_value)
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testContext }"})
    assert response.json() == {"data": {"testContext": "TEST-ASYNC-CONTEXT"}}


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


def test_custom_validation_rule_is_called_by_query_validation(
    mocker, schema, validation_rule
):
    spy_validation_rule = mocker.spy(validation_rule, "__init__")
    app = GraphQL(schema, validation_rules=[validation_rule])
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    spy_validation_rule.assert_called_once()


def test_custom_validation_rules_function_is_set_and_called_on_query_execution(
    mocker, schema, validation_rule
):
    spy_validation_rule = mocker.spy(validation_rule, "__init__")
    get_validation_rules = Mock(return_value=[validation_rule])
    app = GraphQL(schema, validation_rules=get_validation_rules)
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_validation_rules.assert_called_once()
    spy_validation_rule.assert_called_once()


def test_custom_validation_rules_function_is_called_with_context_value(
    schema, validation_rule
):
    get_validation_rules = Mock(return_value=[validation_rule])
    app = GraphQL(
        schema,
        context_value={"test": "TEST-CONTEXT"},
        validation_rules=get_validation_rules,
    )
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_validation_rules.assert_called_once_with({"test": "TEST-CONTEXT"}, ANY, ANY)


def execute_failing_query(app):
    client = TestClient(app)
    client.post("/", json={"query": "{ error }"})


def test_default_logger_is_used_to_log_error_if_custom_is_not_set(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema)
    execute_failing_query(app)
    logging_mock.getLogger.assert_called_once_with("ariadne")


def test_custom_logger_is_used_to_log_query_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
    execute_failing_query(app)
    logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_is_used_to_log_subscription_source_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
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
        logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_is_used_to_log_subscription_resolver_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
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
        logging_mock.getLogger.assert_called_once_with("custom")


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


class CustomExtension(Extension):
    async def resolve(self, next_, parent, info, **kwargs):
        return next_(parent, info, **kwargs).lower()


def test_extension_from_option_are_passed_to_query_executor(schema):
    app = GraphQL(schema, extensions=[CustomExtension])
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "hello, bob!"}}


def test_extensions_function_result_is_passed_to_query_executor(schema):
    def get_extensions(*_):
        return [CustomExtension]

    app = GraphQL(schema, extensions=get_extensions)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "hello, bob!"}}


def test_async_extensions_function_result_is_passed_to_query_executor(schema):
    async def get_extensions(*_):
        return [CustomExtension]

    app = GraphQL(schema, extensions=get_extensions)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "hello, bob!"}}


def middleware(next_fn, *args, **kwargs):
    value = next_fn(*args, **kwargs)
    return f"**{value}**"


def test_middlewares_are_passed_to_query_executor(schema):
    app = GraphQL(schema, middleware=[middleware])
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "**Hello, BOB!**"}}


def test_middleware_function_result_is_passed_to_query_executor(schema):
    def get_middleware(*_):
        return [middleware]

    app = GraphQL(schema, middleware=get_middleware)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "**Hello, BOB!**"}}


def test_async_middleware_function_result_is_passed_to_query_executor(schema):
    async def get_middleware(*_):
        return [middleware]

    app = GraphQL(schema, middleware=get_middleware)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "**Hello, BOB!**"}}
