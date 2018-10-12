import pytest

from ariadne import GraphQLMiddleware


def test_initializing_middleware_without_path_raises_value_error(type_defs):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(None, type_defs=type_defs, resolvers={}, path="")

    assert isinstance(excinfo.value, ValueError)
    assert excinfo.value.args[0] == "path keyword argument can't be empty"


def test_initializing_middleware_with_non_callable_app_raises_type_error(type_defs):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(True, type_defs=type_defs, resolvers={}, path="/")
    assert isinstance(excinfo.value, TypeError)
    assert excinfo.value.args[0] == "first argument must be a callable or None"


def test_initializing_middleware_without_app_raises_type_error(type_defs):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(None, type_defs=type_defs, resolvers={})
    assert isinstance(excinfo.value, TypeError)
    assert excinfo.value.args[0] == (
        "can't set custom path on WSGI middleware without providing "
        "application callable as first argument"
    )


def test_initializing_middleware_with_app_and_root_path_raises_value_error(
    app_mock, type_defs
):
    with pytest.raises(Exception) as excinfo:
        GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers={}, path="/")
    assert isinstance(excinfo.value, ValueError)
    assert excinfo.value.args[0] == (
        "WSGI middleware can't use root path together with application callable"
    )
