import json
from unittest.mock import ANY, Mock

import pytest
from django.test import override_settings

from ariadne.contrib.django.views import GraphQLView


def execute_query(request_factory, schema, query, **kwargs):
    view = GraphQLView.as_view(schema=schema, **kwargs)
    request = request_factory.post(
        "/graphql/", data=query, content_type="application/json"
    )
    response = view(request)
    return json.loads(response.content)


def test_value_error_is_raised_when_view_was_initialized_without_schema(
    request_factory,
):
    with pytest.raises(ValueError):
        execute_query(request_factory, None, {"query": "{ testContext }"})


def test_custom_context_value_is_passed_to_resolvers(request_factory, schema):
    data = execute_query(
        request_factory,
        schema,
        {"query": "{ testContext }"},
        context_value={"test": "TEST-CONTEXT"},
    )
    assert data == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_context_value_function_is_set_and_called_by_app(
    request_factory, schema
):
    get_context_value = Mock(return_value=True)
    execute_query(
        request_factory,
        schema,
        {"query": "{ status }"},
        context_value=get_context_value,
    )
    get_context_value.assert_called_once()


def test_custom_context_value_function_result_is_passed_to_resolvers(
    request_factory, schema
):
    get_context_value = Mock(return_value={"test": "TEST-CONTEXT"})
    data = execute_query(
        request_factory,
        schema,
        {"query": "{ testContext }"},
        context_value=get_context_value,
    )
    assert data == {"data": {"testContext": "TEST-CONTEXT"}}


def test_custom_root_value_is_passed_to_resolvers(request_factory, schema):
    data = execute_query(
        request_factory,
        schema,
        {"query": "{ testRoot }"},
        root_value={"test": "TEST-ROOT"},
    )
    assert data == {"data": {"testRoot": "TEST-ROOT"}}


def test_custom_root_value_function_is_set_and_called_by_app(request_factory, schema):
    get_root_value = Mock(return_value=True)
    execute_query(
        request_factory, schema, {"query": "{ status }"}, root_value=get_root_value
    )
    get_root_value.assert_called_once()


def test_custom_root_value_function_is_called_with_context_value(
    request_factory, schema
):
    get_root_value = Mock(return_value=True)
    execute_query(
        request_factory,
        schema,
        {"query": "{ status }"},
        context_value={"test": "TEST-CONTEXT"},
        root_value=get_root_value,
    )
    get_root_value.assert_called_once_with({"test": "TEST-CONTEXT"}, ANY)


def execute_failing_query(request_factory, schema, **kwargs):
    return execute_query(request_factory, schema, {"query": "{ error }"}, **kwargs)


def test_default_logger_is_used_to_log_error_if_custom_is_not_set(
    request_factory, schema, mocker
):
    logging_mock = mocker.patch("ariadne.logger.logging")
    execute_failing_query(request_factory, schema)
    logging_mock.getLogger.assert_called_once_with("ariadne")


def test_custom_logger_is_used_to_log_query_error(request_factory, schema, mocker):
    logging_mock = mocker.patch("ariadne.logger.logging")
    execute_failing_query(request_factory, schema, logger="custom")
    logging_mock.getLogger.assert_called_once_with("custom")


def test_custom_error_formatter_is_used_to_format_error(request_factory, schema):
    error_formatter = Mock(return_value=True)
    execute_failing_query(request_factory, schema, error_formatter=error_formatter)
    error_formatter.assert_called_once()


@override_settings(DEBUG=True)
def test_error_formatter_is_called_with_debug_enabled_flag(request_factory, schema):
    error_formatter = Mock(return_value=True)
    execute_failing_query(request_factory, schema, error_formatter=error_formatter)
    error_formatter.assert_called_once_with(ANY, True)


@override_settings(DEBUG=False)
def test_error_formatter_is_called_with_debug_disabled_flag(request_factory, schema):
    error_formatter = Mock(return_value=True)
    execute_failing_query(request_factory, schema, error_formatter=error_formatter)
    error_formatter.assert_called_once_with(ANY, False)
