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


def test_custom_error_formatter_is_set_and_used_by_app(schema):
    format_error = Mock(return_value=True)
    app = GraphQL(schema, format_error=format_error)
    execute_failing_query(app)
    format_error.assert_called_once()


def test_error_formatter_is_called_with_debug_enabled_flag(schema):
    format_error = Mock(return_value=True)
    app = GraphQL(schema, debug=True, format_error=format_error)
    execute_failing_query(app)
    format_error.assert_called_once_with(ANY, True)


def test_error_formatter_is_called_with_debug_disabled_flag(schema):
    format_error = Mock(return_value=True)
    app = GraphQL(schema, debug=False, format_error=format_error)
    execute_failing_query(app)
    format_error.assert_called_once_with(ANY, False)
