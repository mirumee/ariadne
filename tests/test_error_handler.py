from unittest.mock import Mock

import pytest
from graphql import graphql_sync

from ariadne import QueryType, make_executable_schema
from ariadne import default_error_handler, get_error_extension


@pytest.fixture
def erroring_resolvers():
    query = QueryType()

    @query.field("hello")
    def resolve_hello_with_context_and_attribute_error(*_):
        # pylint: disable=undefined-variable, unused-variable
        test_int = 123
        test_str = "test"
        test_dict = {"test": "dict"}
        test_obj = query
        test_undefined.error()  # trigger attr not found error

    return query


@pytest.fixture
def schema(type_defs, resolvers, erroring_resolvers, subscriptions):
    return make_executable_schema(
        type_defs, [resolvers, erroring_resolvers, subscriptions]
    )


def test_default_error_handler_is_not_extending_error_by_default(schema):
    result = graphql_sync(schema, "{ hello }")
    error = default_error_handler(result)[0]
    assert not error.get("extensions")


def test_default_error_handler_extracts_errors_from_result(schema):
    result = graphql_sync(schema, "{ hello }")
    assert default_error_handler(result)


def test_default_error_handler_extends_error_with_traceback(schema):
    result = graphql_sync(schema, "{ hello }")
    error = default_error_handler(result, extend_exception=True)[0]
    assert error["extensions"]["exception"]["traceback"]


def test_default_error_handler_extends_error_with_context(schema):
    result = graphql_sync(schema, "{ hello }")
    error = default_error_handler(result, extend_exception=True)[0]
    assert error["extensions"]["exception"]["context"]


def test_default_error_handler_fills_context_with_reprs_of_python_context(
    schema, erroring_resolvers
):
    result = graphql_sync(schema, "{ hello }")
    error = default_error_handler(result, extend_exception=True)[0]
    context = error["extensions"]["exception"]["context"]

    assert context["test_int"] == repr(123)
    assert context["test_str"] == repr("test")
    assert context["test_dict"] == repr({"test": "dict"})
    assert context["test_obj"] == repr(erroring_resolvers)


def test_default_error_handler_is_not_extending_plain_graphql_error(schema):
    result = graphql_sync(schema, "{ error }")
    error = default_error_handler(result, extend_exception=True)[0]
    assert error["extensions"]["exception"] is None


def test_error_extension_is_not_available_for_error_without_traceback():
    error = Mock(__traceback__=None, spec=["__traceback__"])
    assert get_error_extension(error) is None
