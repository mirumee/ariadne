from reprlib import repr  # pylint: disable=redefined-builtin
from unittest.mock import Mock

import pytest
from graphql import graphql_sync

from ariadne import QueryType, make_executable_schema
from ariadne.format_error import (
    format_error,
    get_error_extension,
    get_formatted_error_context,
)


@pytest.fixture
def failing_repr_mock():
    return Mock(__repr__=Mock(side_effect=KeyError("test")), spec=["__repr__"])


@pytest.fixture
def erroring_resolvers(failing_repr_mock):
    query = QueryType()

    @query.field("hello")
    def resolve_hello_with_context_and_attribute_error(*_):
        # pylint: disable=undefined-variable, unused-variable
        test_int = 123
        test_str = "test"
        test_dict = {"test": "dict"}
        test_obj = query
        test_failing_repr = failing_repr_mock
        test_undefined.error()  # trigger attr not found error

    return query


@pytest.fixture
def schema(type_defs, resolvers, erroring_resolvers, subscriptions):
    return make_executable_schema(
        type_defs, [resolvers, erroring_resolvers, subscriptions]
    )


def test_default_formatter_is_not_extending_error_by_default(schema):
    result = graphql_sync(schema, "{ hello }")
    error = format_error(result.errors[0])
    assert not error.get("extensions")


def test_default_formatter_extends_error_with_stacktrace(schema):
    result = graphql_sync(schema, "{ hello }")
    error = format_error(result.errors[0], debug=True)
    assert error["extensions"]["exception"]["stacktrace"]


def test_default_formatter_extends_error_with_context(schema):
    result = graphql_sync(schema, "{ hello }")
    error = format_error(result.errors[0], debug=True)
    assert error["extensions"]["exception"]["context"]


def test_default_formatter_fills_context_with_reprs_of_python_context(
    schema, erroring_resolvers, failing_repr_mock
):
    result = graphql_sync(schema, "{ hello }")
    error = format_error(result.errors[0], debug=True)
    context = error["extensions"]["exception"]["context"]

    assert context["test_int"] == repr(123)
    assert context["test_str"] == repr("test")
    assert context["test_dict"] == repr({"test": "dict"})
    assert context["test_failing_repr"] == repr(failing_repr_mock)
    assert context["test_obj"] == repr(erroring_resolvers)


def test_default_formatter_is_not_extending_plain_graphql_error(schema):
    result = graphql_sync(schema, "{ error }")
    error = format_error(result.errors[0], debug=True)
    assert error["extensions"]["exception"] is None


def test_error_extension_is_not_available_for_error_without_traceback():
    error = Mock(__traceback__=None, spec=["__traceback__"])
    assert get_error_extension(error) is None


def test_incomplete_traceback_is_handled_by_context_extractor():
    error = Mock(__traceback__=None, spec=["__traceback__"])
    assert get_formatted_error_context(error) is None
