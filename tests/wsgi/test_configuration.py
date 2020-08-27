import json
from io import BytesIO
from unittest.mock import ANY, Mock

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from ariadne.constants import DATA_TYPE_JSON
from ariadne.types import ExtensionSync
from ariadne.wsgi import GraphQL


# Add json method to keep test similar to ASGI
class Response(BaseResponse):
    def json(self):
        return json.loads(self.data)


# Add TestClient to keep test similar to ASGI
class TestClient(Client):
    __test__ = False

    def __init__(self, app):
        super().__init__(app, Response)


def test_custom_context_value_is_passed_to_resolvers(schema):
    app = GraphQL(schema, context_value={"test": "TEST-CONTEXT"})
    _, result = app.execute_query({}, {"query": "{ testContext }"})
    assert result == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_context_value_function_is_set_and_called_by_app(schema):
    get_context_value = Mock(return_value=True)
    app = GraphQL(schema, context_value=get_context_value)
    app.execute_query({}, {"query": "{ status }"})
    get_context_value.assert_called_once()


def test_custom_context_value_function_is_called_with_request_value(schema):
    get_context_value = Mock(return_value=True)
    app = GraphQL(schema, context_value=get_context_value)
    request = {"CONTENT_TYPE": DATA_TYPE_JSON}
    app.execute_query(request, {"query": "{ status }"})
    get_context_value.assert_called_once_with(request)


def test_custom_context_value_function_result_is_passed_to_resolvers(schema):
    get_context_value = Mock(return_value={"test": "TEST-CONTEXT"})
    app = GraphQL(schema, context_value=get_context_value)
    _, result = app.execute_query({}, {"query": "{ testContext }"})
    assert result == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_root_value_is_passed_to_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    _, result = app.execute_query({}, {"query": "{ testRoot }"})
    assert result == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_function_is_set_and_called_by_app(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    app.execute_query({}, {"query": "{ status }"})
    get_root_value.assert_called_once()


def test_custom_root_value_function_is_called_with_context_value(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(
        schema, context_value={"test": "TEST-CONTEXT"}, root_value=get_root_value
    )
    app.execute_query({}, {"query": "{ status }"})
    get_root_value.assert_called_once_with({"test": "TEST-CONTEXT"}, ANY)


def test_custom_validation_rule_is_called_by_query_validation(
    mocker, schema, validation_rule
):
    spy_validation_rule = mocker.spy(validation_rule, "__init__")
    app = GraphQL(schema, validation_rules=[validation_rule])
    app.execute_query({}, {"query": "{ status }"})
    spy_validation_rule.assert_called_once()


def test_custom_validation_rules_function_is_set_and_called_on_query_execution(
    mocker, schema, validation_rule
):
    spy_validation_rule = mocker.spy(validation_rule, "__init__")
    get_validation_rules = Mock(return_value=[validation_rule])
    app = GraphQL(schema, validation_rules=get_validation_rules)
    app.execute_query({}, {"query": "{ status }"})
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
    app.execute_query({}, {"query": "{ status }"})
    get_validation_rules.assert_called_once_with({"test": "TEST-CONTEXT"}, ANY, ANY)


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


class CustomExtension(ExtensionSync):
    def resolve(self, next_, parent, info, **kwargs):
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


def middleware(next_fn, *args, **kwargs):
    value = next_fn(*args, **kwargs)
    return f"**{value}**"


def test_middlewares_are_passed_to_query_executor(schema):
    app = GraphQL(schema, middleware=[middleware])
    _, result = app.execute_query({}, {"query": '{ hello(name: "BOB") }'})
    assert result == {"data": {"hello": "**Hello, BOB!**"}}


def test_middleware_function_result_is_passed_to_query_executor(schema):
    def get_middleware(*_):
        return [middleware]

    app = GraphQL(schema, middleware=get_middleware)
    _, result = app.execute_query({}, {"query": '{ hello(name: "BOB") }'})
    assert result == {"data": {"hello": "**Hello, BOB!**"}}
