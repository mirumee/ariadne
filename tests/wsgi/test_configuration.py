import json
from io import BytesIO
from unittest.mock import ANY, Mock

from ariadne.constants import DATA_TYPE_JSON
from ariadne.wsgi import GraphQL


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
