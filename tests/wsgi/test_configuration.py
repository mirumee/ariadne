import json
from io import BytesIO
from unittest.mock import ANY, Mock

from ariadne.constants import DATA_TYPE_JSON
from ariadne.wsgi import GraphQL


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


def test_custom_error_formatter_is_set_and_used_by_app(schema):
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
