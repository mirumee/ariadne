from unittest.mock import ANY, Mock

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


def execute_failing_query(app):
    client = TestClient(app)
    client.post("/", json={"query": "{ error }"})


def test_custom_error_handler_is_set_and_used_by_app(schema):
    error_handler = Mock(return_value=True)
    app = GraphQL(schema, error_handler=error_handler)
    execute_failing_query(app)
    error_handler.assert_called_once()


def test_error_handler_is_called_with_debug_enabled(schema):
    error_handler = Mock(return_value=True)
    app = GraphQL(schema, debug=True, error_handler=error_handler)
    execute_failing_query(app)
    error_handler.assert_called_once_with(ANY, True)


def test_error_handler_is_called_with_debug_disabled(schema):
    error_handler = Mock(return_value=True)
    app = GraphQL(schema, debug=False, error_handler=error_handler)
    execute_failing_query(app)
    error_handler.assert_called_once_with(ANY, False)
