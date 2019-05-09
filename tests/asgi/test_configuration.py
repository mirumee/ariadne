from unittest.mock import ANY, Mock

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL


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


def test_custom_root_value_is_passed_to_resolvers(schema):
    app = GraphQL(schema, root_value={"test": "TEST-ROOT"})
    client = TestClient(app)
    response = client.post("/", json={"query": "{ testRoot }"})
    assert response.json() == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_function_is_set_and_called_by_app(schema):
    get_root_value = Mock(return_value=True)
    app = GraphQL(schema, root_value=get_root_value)
    client = TestClient(app)
    client.post("/", json={"query": "{ status }"})
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


def test_custom_error_formatter_is_set_and_used_by_app(schema):
    error_formatter = Mock(return_value=True)
    app = GraphQL(schema, error_formatter=error_formatter)
    execute_failing_query(app)
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
