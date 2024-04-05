import json
from io import BytesIO
from unittest.mock import ANY, Mock

import pytest
from graphql import (
    GraphQLError,
    parse,
)
from graphql_sync_dataloaders import DeferredExecutionContext, SyncDataLoader
from werkzeug.test import Client
from werkzeug.wrappers import Response

from ariadne import QueryType, make_executable_schema
from ariadne.constants import DATA_TYPE_JSON, HttpStatusResponse
from ariadne.types import Extension
from ariadne.wsgi import GraphQL


# Add TestClient to keep test similar to ASGI
class TestClient(Client):
    __test__ = False

    def __init__(self, app):
        super().__init__(app, Response)


def test_custom_context_value_is_passed_to_resolvers(schema):
    app = GraphQL(schema, context_value={"test": "TEST-CONTEXT"})
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ testContext }"},
    )
    assert result == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_context_value_function_is_set_and_called_by_app(schema):
    get_context_value = Mock(return_value=True)
    app = GraphQL(schema, context_value=get_context_value)
    app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ status }"},
    )
    get_context_value.assert_called_once()


def test_custom_context_value_function_is_called_with_request_value(schema):
    get_context_value = Mock(return_value=True)
    app = GraphQL(schema, context_value=get_context_value)
    request = {"CONTENT_TYPE": DATA_TYPE_JSON, "REQUEST_METHOD": "POST"}
    app.execute_query(request, {"query": "{ status }"})
    get_context_value.assert_called_once_with(request, {"query": "{ status }"})


def test_custom_context_value_function_result_is_passed_to_resolvers(schema):
    get_context_value = Mock(return_value={"test": "TEST-CONTEXT"})
    app = GraphQL(schema, context_value=get_context_value)
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ testContext }"},
    )
    assert result == {"data": {"testContext": "TEST-CONTEXT"}}


def test_warning_is_raised_if_custom_context_value_function_has_deprecated_signature(
    schema,
):
    def get_context_value(request):
        return {"request": request}

    app = GraphQL(schema, context_value=get_context_value)

    with pytest.deprecated_call():
        app.execute_query(
            {"REQUEST_METHOD": "POST"},
            {"query": "{ status }"},
        )


def test_custom_root_value_is_passed_to_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ testRoot }"},
    )
    assert result == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_function_is_set_and_called_by_app(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ status }"},
    )
    get_root_value.assert_called_once()


def test_custom_root_value_function_is_called_with_context_value(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(
        schema, context_value={"test": "TEST-CONTEXT"}, root_value=get_root_value
    )
    app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ status }"},
    )
    get_root_value.assert_called_once_with({"test": "TEST-CONTEXT"}, None, None, ANY)


def test_warning_is_raised_if_custom_root_value_function_has_deprecated_signature(
    schema,
):
    def get_root_value(_context, _document):
        return True

    app = GraphQL(
        schema, context_value={"test": "TEST-CONTEXT"}, root_value=get_root_value
    )

    with pytest.deprecated_call():
        app.execute_query(
            {"REQUEST_METHOD": "POST"},
            {"query": "{ status }"},
        )


def test_custom_query_parser_is_used(schema):
    mock_parser = Mock(return_value=parse("{ status }"))
    app = GraphQL(schema, query_parser=mock_parser)
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ testContext }"},
    )
    assert result == {"data": {"status": True}}
    mock_parser.assert_called_once()


@pytest.mark.parametrize(
    ("errors"),
    [
        ([]),
        ([GraphQLError("Nope")]),
    ],
)
def test_custom_query_validator_is_used(schema, errors):
    mock_validator = Mock(return_value=errors)
    app = GraphQL(schema, query_validator=mock_validator)
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ testContext }"},
    )
    if errors:
        assert result == {"errors": [{"message": "Nope"}]}
    else:
        assert result == {"data": {"testContext": None}}
    mock_validator.assert_called_once()


def test_custom_validation_rule_is_called_by_query_validation(
    mocker, schema, validation_rule
):
    spy_validation_rule = mocker.spy(validation_rule, "__init__")
    app = GraphQL(schema, validation_rules=[validation_rule])
    app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ status }"},
    )
    spy_validation_rule.assert_called_once()


def test_custom_validation_rules_function_is_set_and_called_on_query_execution(
    mocker, schema, validation_rule
):
    spy_validation_rule = mocker.spy(validation_rule, "__init__")
    get_validation_rules = Mock(return_value=[validation_rule])
    app = GraphQL(schema, validation_rules=get_validation_rules)
    app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ status }"},
    )
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
    app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": "{ status }"},
    )
    get_validation_rules.assert_called_once_with({"test": "TEST-CONTEXT"}, ANY, ANY)


def test_query_over_get_is_executed_if_enabled(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=True)
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": "query={status}",
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.OK.value,
        [("Content-Type", "application/json; charset=UTF-8")],
    )
    assert json.loads(response[0]) == {"data": {"status": True}}


def test_query_over_get_is_executed_with_variables(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=True)
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": (
                "query=query Hello($name:String) {hello(name: $name)}"
                "&operationName=Hello"
                '&variables={"name": "John"}'
            ),
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.OK.value,
        [("Content-Type", "application/json; charset=UTF-8")],
    )
    assert json.loads(response[0]) == {"data": {"hello": "Hello, John!"}}


def test_query_over_get_is_executed_without_operation_name(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=True)
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": (
                "query=query Hello($name:String) {hello(name: $name)}"
                '&variables={"name": "John"}'
            ),
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.OK.value,
        [("Content-Type", "application/json; charset=UTF-8")],
    )
    assert json.loads(response[0]) == {"data": {"hello": "Hello, John!"}}


def test_query_over_get_fails_if_operation_name_is_invalid(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=True)
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": (
                "query=query Hello($name:String) {hello(name: $name)}"
                "&operationName=Invalid"
                '&variables={"name": "John"}'
            ),
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.BAD_REQUEST.value,
        [("Content-Type", "application/json; charset=UTF-8")],
    )
    assert json.loads(response[0]) == {
        "errors": [
            {
                "message": (
                    "Operation 'Invalid' is not defined or is not of a 'query' type."
                )
            }
        ]
    }


def test_query_over_get_fails_if_operation_is_mutation(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=True)
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": (
                "query=mutation Echo($text:String!) {echo(text: $text)}"
                "&operationName=Echo"
                '&variables={"text": "John"}'
            ),
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.BAD_REQUEST.value,
        [("Content-Type", "application/json; charset=UTF-8")],
    )
    assert json.loads(response[0]) == {
        "errors": [
            {
                "message": (
                    "Operation 'Echo' is not defined or is not of a 'query' type."
                )
            }
        ]
    }


def test_query_over_get_fails_if_variables_are_not_json_serialized(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=True)
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": (
                "query=query Hello($name:String) {hello(name: $name)}"
                "&operationName=Hello"
                '&variables={"name" "John"}'
            ),
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.BAD_REQUEST.value,
        [("Content-Type", "text/plain; charset=UTF-8")],
    )
    assert response[0] == b"Variables query arg is not a valid JSON"


def test_query_over_get_is_not_executed_if_not_enabled(schema):
    send_response = Mock()
    app = GraphQL(schema, execute_get_queries=False)
    app.handle_request(
        {
            "REQUEST_METHOD": "GET",
            "QUERY_STRING": "query={status}",
        },
        send_response,
    )
    send_response.assert_called_once_with(
        HttpStatusResponse.OK.value, [("Content-Type", "text/html; charset=UTF-8")]
    )


def execute_failing_query(app):
    data = json.dumps({"query": "{ error }"})
    app(
        {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": DATA_TYPE_JSON,
            "CONTENT_LENGTH": len(data),
            "wsgi.input": BytesIO(data.encode("utf-8")),
        },
        Mock(),
    )


def test_default_logger_is_used_to_log_error_if_custom_is_not_set(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema)
    execute_failing_query(app)
    logging_mock.getLogger.assert_called_once_with("ariadne")


def test_custom_logger_is_used_to_log_error(schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    app = GraphQL(schema, logger="custom")
    execute_failing_query(app)
    logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_logger_instance_is_used_to_log_error(schema):
    logger_instance_mock = Mock()
    app = GraphQL(schema, logger=logger_instance_mock)
    execute_failing_query(app)
    logger_instance_mock.error.assert_called()


def test_custom_error_formatter_is_used_to_format_error(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    execute_failing_query(app)
    error_formatter.assert_called_once()


def test_error_formatter_is_called_with_debug_enabled_flag(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, debug=True, error_formatter=error_formatter)
    execute_failing_query(app)
    error_formatter.assert_called_once_with(ANY, True)


def test_error_formatter_is_called_with_debug_disabled_flag(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, debug=False, error_formatter=error_formatter)
    execute_failing_query(app)
    error_formatter.assert_called_once_with(ANY, False)


class CustomExtension(Extension):
    def resolve(self, next_, obj, info, **kwargs):
        return next_(obj, info, **kwargs).lower()


def test_extension_from_option_are_passed_to_query_executor(schema):
    app = GraphQL(schema, extensions=[CustomExtension])
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json == {"data": {"hello": "hello, bob!"}}


def test_extensions_function_result_is_passed_to_query_executor(schema):
    def get_extensions(*_):
        return [CustomExtension]

    app = GraphQL(schema, extensions=get_extensions)
    client = TestClient(app)
    response = client.post("/", json={"query": '{ hello(name: "BOB") }'})
    assert response.json == {"data": {"hello": "hello, bob!"}}


def middleware(next_fn, *args, **kwargs):
    value = next_fn(*args, **kwargs)
    return f"**{value}**"


def test_middlewares_are_passed_to_query_executor(schema):
    app = GraphQL(schema, middleware=[middleware])
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": '{ hello(name: "BOB") }'},
    )
    assert result == {"data": {"hello": "**Hello, BOB!**"}}


def test_middleware_function_result_is_passed_to_query_executor(schema):
    def get_middleware(*_):
        return [middleware]

    app = GraphQL(schema, middleware=get_middleware)
    _, result = app.execute_query(
        {"REQUEST_METHOD": "POST"},
        {"query": '{ hello(name: "BOB") }'},
    )
    assert result == {"data": {"hello": "**Hello, BOB!**"}}


def test_wsgi_app_supports_sync_dataloader_with_custom_execution_context():
    type_defs = """
        type Query {
            test(arg: ID!): String!
        }
    """

    def dataloader_fn(keys):
        return keys

    dataloader = SyncDataLoader(dataloader_fn)

    query = QueryType()
    query.set_field("test", lambda *_, arg: dataloader.load(arg))

    schema = make_executable_schema(
        type_defs,
        [query],
    )

    app = GraphQL(schema, execution_context_class=DeferredExecutionContext)
    client = TestClient(app)

    response = client.post(
        "/", json={"query": "{ test1: test(arg: 1), test2: test(arg: 2) }"}
    )
    assert response.json == {"data": {"test1": "1", "test2": "2"}}
