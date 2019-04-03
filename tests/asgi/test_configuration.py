from unittest.mock import ANY, Mock

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


def execute_failing_query(app):
    client = TestClient(app)
    client.post("/", json={"query": "{ error }"})


def test_custom_error_formatter_is_set_and_used_by_app(schema):
    format_error = Mock(return_value=True)
    app = GraphQL(schema, format_error=format_error)
    execute_failing_query(app)
    format_error.assert_called_once()


def test_error_formatter_is_called_with_debug_enabled(schema):
    format_error = Mock(return_value=True)
    app = GraphQL(schema, debug=True, format_error=format_error)
    execute_failing_query(app)
    format_error.assert_called_once_with(ANY, True)


def test_error_formatter_is_called_with_debug_disabled(schema):
    format_error = Mock(return_value=True)
    app = GraphQL(schema, debug=False, format_error=format_error)
    execute_failing_query(app)
    format_error.assert_called_once_with(ANY, False)
