import time
from datetime import timedelta
from http import HTTPStatus
from unittest.mock import ANY, Mock

import pytest
from graphql import GraphQLError, parse
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import (
    GraphQLHTTPHandler,
    GraphQLTransportWSHandler,
    GraphQLWSHandler,
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
    get_context_value.assert_called_once_with(ANY, {"query": "{ status }"})


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


def test_custom_deprecated_context_value_function_raises_warning_by_query(
    schema,
):
    def get_context_value(request):
        return {"request": request}

    app = GraphQL(schema, context_value=get_context_value)
    client = TestClient(app)

    with pytest.deprecated_call():
        client.post("/", json={"query": "{ status }"})


def test_custom_root_value_is_passed_to_query_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testRoot }"})
    assert response.json() == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_is_passed_to_subscription_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { testRoot }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["payload"] == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_is_passed_to_subscription_resolvers_graphql_transport_ws(
    schema,
):
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        root_value={"test": "TEST-ROOT"},
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { testRoot }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["payload"] == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_function_is_called_by_query(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_root_value.assert_called_once()


def test_custom_deprecated_root_value_function_raises_warning_by_query(
    schema,
):
    def get_root_value(_context, _document):
        return True

    app = GraphQL(
        schema, context_value={"test": "TEST-CONTEXT"}, root_value=get_root_value
    )
    client = TestClient(app)

    with pytest.deprecated_call():
        client.post("/", json={"query": "{ status }"})


def test_custom_root_value_function_is_called_by_subscription(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { ping }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        get_root_value.assert_called_once()


def test_custom_deprecated_root_value_function_raises_warning_by_subscription(schema):
    def get_root_value(_context, _document):
        return True

    app = GraphQL(schema, root_value=get_root_value)
    client = TestClient(app)

    with pytest.deprecated_call():
        with client.websocket_connect("/", ["graphql-ws"]) as ws:
            ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
            ws.send_json(
                {
                    "type": GraphQLWSHandler.GQL_START,
                    "id": "test1",
                    "payload": {"query": "subscription { ping }"},
                }
            )
            response = ws.receive_json()
            assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
            response = ws.receive_json()
            assert response["type"] == GraphQLWSHandler.GQL_DATA


def test_custom_root_value_function_is_called_by_subscription_graphql_transport_ws(
    schema,
):
    get_root_value = Mock(return_value=True)
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        root_value=get_root_value,
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
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
        get_root_value.assert_called_once()


def test_custom_deprecated_root_value_function_raises_warning_by_subscription_graphql_transport_ws(  # noqa: E501
    schema,
):
    def get_root_value(_context, _document):
        return True

    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        root_value=get_root_value,
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)

    with pytest.deprecated_call():
        with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
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


def test_custom_root_value_function_is_called_with_context_value(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(
        schema,
        context_value={"test": "TEST-CONTEXT"},
        root_value=get_root_value,
    )
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
    get_root_value.assert_called_once_with({"test": "TEST-CONTEXT"}, None, None, ANY)


def test_custom_query_parser_is_used_for_http_query(schema):
    mock_parser = Mock(return_value=parse("{ status }"))
    app = GraphQL(schema, query_parser=mock_parser)
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testContext }"})
    assert response.json() == {"data": {"status": True}}
    mock_parser.assert_called_once()


@pytest.mark.parametrize(
    ("errors"),
    [
        ([]),
        ([GraphQLError("Nope")]),
    ],
)
def test_custom_query_validator_is_used_for_http_query_error(schema, errors):
    mock_validator = Mock(return_value=errors)
    app = GraphQL(schema, query_validator=mock_validator)
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testContext }"})
    if errors:
        assert response.json() == {"errors": [{"message": "Nope"}]}
    else:
        assert response.json() == {"data": {"testContext": None}}
    mock_validator.assert_called_once()


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


def test_query_over_get_is_executed_if_enabled(schema):
    app = GraphQL(schema, execute_get_queries=True)
    client = TestClient(app)
    response = client.get("/?query={status}")
    assert response.json() == {"data": {"status": True}}


def test_query_over_get_is_executed_with_variables(schema):
    app = GraphQL(schema, execute_get_queries=True)
    client = TestClient(app)
    response = client.get(
        "/?query=query Hello($name:String) {hello(name: $name)}"
        "&operationName=Hello"
        '&variables={"name": "John"}'
    )
    assert response.json() == {"data": {"hello": "Hello, John!"}}


def test_query_over_get_is_executed_without_operation_name(schema):
    app = GraphQL(schema, execute_get_queries=True)
    client = TestClient(app)
    response = client.get(
        "/?query=query Hello($name:String) {hello(name: $name)}"
        '&variables={"name": "John"}'
    )
    assert response.json() == {"data": {"hello": "Hello, John!"}}


def test_query_over_get_fails_if_operation_name_is_invalid(schema):
    app = GraphQL(schema, execute_get_queries=True)
    client = TestClient(app)
    response = client.get(
        "/?query=query Hello($name:String) {hello(name: $name)}"
        "&operationName=Invalid"
        '&variables={"name": "John"}'
    )
    assert response.json() == {
        "errors": [
            {
                "message": (
                    "Operation 'Invalid' is not defined or is not of a 'query' type."
                )
            }
        ]
    }


def test_query_over_get_fails_if_operation_is_mutation(schema):
    app = GraphQL(schema, execute_get_queries=True)
    client = TestClient(app)
    response = client.get(
        "/?query=mutation Echo($text:String!) {echo(text: $text)}"
        "&operationName=Echo"
        '&variables={"text": "John"}'
    )
    assert response.json() == {
        "errors": [
            {
                "message": (
                    "Operation 'Echo' is not defined or is not of a 'query' type."
                )
            }
        ]
    }


def test_query_over_get_fails_if_variables_are_not_json_serialized(schema):
    app = GraphQL(schema, execute_get_queries=True)
    client = TestClient(app)
    response = client.get(
        "/?query=query Hello($name:String) {hello(name: $name)}"
        "&operationName=Hello"
        '&variables={"name" "John"}'
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.content == b"Variables query arg is not a valid JSON"


def test_query_over_get_is_not_executed_if_not_enabled(schema):
    app = GraphQL(schema, execute_get_queries=False)
    client = TestClient(app)
    response = client.get("/?query={ status }")
    assert response.status_code == HTTPStatus.OK
    assert response.headers["CONTENT-TYPE"] == "text/html; charset=utf-8"


def execute_failing_query(app):
    client = TestClient(app)
    client.post("/", json={"query": "{ error }"})


def test_default_logger_is_used_to_log_error_if_custom_is_not_set(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema)
    execute_failing_query(app)
    logging_mock.getLogger.assert_called_once_with("ariadne")


def test_custom_logger_instance_is_used_to_log_error(schema):
    logger_instance_mock = Mock()
    app = GraphQL(schema, logger=logger_instance_mock)
    execute_failing_query(app)
    logger_instance_mock.error.assert_called()


def test_custom_logger_is_used_to_log_query_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
    execute_failing_query(app)
    logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_is_used_to_log_subscription_source_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { sourceError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_is_used_to_log_subscription_source_error_graphql_transport_ws(
    schema, mocker
):
    logging_mock = mocker.patch("ariadne.logger.logging")
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        logger="custom",
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { sourceError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_is_used_to_log_subscription_resolver_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { resolverError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_is_used_to_log_subscription_resolver_error_graphql_transport_ws(
    schema, mocker
):
    logging_mock = mocker.patch("ariadne.logger.logging")
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        logger="custom",
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { resolverError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
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
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription {"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_ERROR
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_syntax_error_graphql_transport_ws(  # noqa E501
    schema,
):
    error_formatter = Mock(return_value=True)
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        error_formatter=error_formatter,
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription {"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_ERROR
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_source_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { sourceError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_source_error_graphql_transport_ws(  # noqa E501
    schema,
):
    error_formatter = Mock(return_value=True)
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        error_formatter=error_formatter,
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { sourceError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_resolver_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-ws"]) as ws:
        ws.send_json({"type": GraphQLWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLWSHandler.GQL_START,
                "id": "test1",
                "payload": {"query": "subscription { resolverError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLWSHandler.GQL_DATA
        assert response["id"] == "test1"
        error_formatter.assert_called_once()


def test_custom_error_formatter_is_used_to_format_subscription_resolver_error_graphql_transport_ws(  # noqa E501
    schema,
):
    error_formatter = Mock(return_value=True)
    websocket_handler = GraphQLTransportWSHandler()
    app = GraphQL(
        schema,
        error_formatter=error_formatter,
        websocket_handler=websocket_handler,
    )
    client = TestClient(app)
    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.send_json(
            {
                "type": GraphQLTransportWSHandler.GQL_SUBSCRIBE,
                "id": "test1",
                "payload": {"query": "subscription { resolverError }"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_CONNECTION_ACK
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_NEXT
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
    def resolve(self, next_, obj, info, **kwargs):
        return next_(obj, info, **kwargs).lower()


def test_extension_from_option_are_passed_to_query_executor(schema):
    http_handler = GraphQLHTTPHandler(extensions=[CustomExtension])
    app = GraphQL(schema, http_handler=http_handler)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "hello, bob!"}}


def test_extensions_function_result_is_passed_to_query_executor(schema):
    def get_extensions(*_):
        return [CustomExtension]

    http_handler = GraphQLHTTPHandler(extensions=get_extensions)
    app = GraphQL(schema, http_handler=http_handler)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "hello, bob!"}}


def test_async_extensions_function_result_is_passed_to_query_executor(schema):
    async def get_extensions(*_):
        return [CustomExtension]

    http_handler = GraphQLHTTPHandler(extensions=get_extensions)
    app = GraphQL(schema, http_handler=http_handler)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "hello, bob!"}}


def middleware(next_fn, *args, **kwargs):
    value = next_fn(*args, **kwargs)
    return f"**{value}**"


def test_middlewares_are_passed_to_query_executor(schema):
    http_handler = GraphQLHTTPHandler(middleware=[middleware])
    app = GraphQL(schema, http_handler=http_handler)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "**Hello, BOB!**"}}


def test_middleware_function_result_is_passed_to_query_executor(schema):
    def get_middleware(*_):
        return [middleware]

    http_handler = GraphQLHTTPHandler(middleware=get_middleware)
    app = GraphQL(schema, http_handler=http_handler)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "**Hello, BOB!**"}}


def test_async_middleware_function_result_is_passed_to_query_executor(schema):
    async def get_middleware(*_):
        return [middleware]

    http_handler = GraphQLHTTPHandler(middleware=get_middleware)
    app = GraphQL(schema, http_handler=http_handler)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json() == {"data": {"hello": "**Hello, BOB!**"}}


def test_init_wait_timeout_graphql_transport_ws(
    schema,
):
    websocket_handler = GraphQLTransportWSHandler(
        connection_init_wait_timeout=timedelta(minutes=0)
    )
    app = GraphQL(schema, websocket_handler=websocket_handler)
    client = TestClient(app)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
            time.sleep(0.1)
            ws.receive_json()

    assert exc_info.value.code == 4408


@pytest.mark.xfail(reason="sometimes fails due to a race condition")
def test_handle_connection_init_timeout_handler_executed_graphql_transport_ws(
    schema,
):
    websocket_handler = GraphQLTransportWSHandler(
        connection_init_wait_timeout=timedelta(seconds=0.2)
    )
    app = GraphQL(schema, websocket_handler=websocket_handler)

    client = TestClient(app)

    with client.websocket_connect("/", ["graphql-transport-ws"]) as ws:
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_CONNECTION_INIT})
        ws.receive_json()
        time.sleep(0.5)
        ws.send_json({"type": GraphQLTransportWSHandler.GQL_PING})
        response = ws.receive_json()
        assert response["type"] == GraphQLTransportWSHandler.GQL_PONG
