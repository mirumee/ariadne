import pytest

from ariadne.wsgi import GraphQLMiddleware


def test_initializing_middleware_without_path_raises_value_error(schema):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(lambda *_: None, schema, path="")

    assert isinstance(excinfo.value, ValueError)
    assert excinfo.value.args[0] == "path can't be empty"


def test_initializing_middleware_with_non_callable_app_raises_type_error(schema):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(True, schema, path="/")
    assert isinstance(excinfo.value, TypeError)
    assert excinfo.value.args[0] == "app must be a callable WSGI application"


def test_initializing_middleware_without_app_raises_type_error(schema):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(None, schema)
    assert isinstance(excinfo.value, TypeError)
    assert excinfo.value.args[0] == ("app must be a callable WSGI application")


def test_initializing_middleware_with_app_and_root_path_raises_value_error(
    app_mock, schema
):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(app_mock, schema, path="/")
    assert isinstance(excinfo.value, ValueError)
    assert excinfo.value.args[0] == (
        "WSGI middleware can't use root path together with application callable"
    )
