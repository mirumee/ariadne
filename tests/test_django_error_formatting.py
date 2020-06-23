from unittest import mock

import django.core.exceptions
import rest_framework.exceptions
from graphql import GraphQLError

from ariadne.contrib.django.format_error import (
    format_graphql_error,
    extract_original_error,
    get_full_django_validation_error_details,
    is_rest_framework_enabled,
)


def test_extract_original_error_no_original_error():
    graphql_error = GraphQLError(message="Meow")
    extracted_error = extract_original_error(graphql_error)
    assert extracted_error == graphql_error


def test_extract_original_error_single_layer():
    original_error = django.core.exceptions.ValidationError("Woof")
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = original_error
    extracted_error = extract_original_error(graphql_error)
    assert extracted_error == original_error


def test_extract_original_error_many_layers():
    original_error = django.core.exceptions.PermissionDenied("Moo")
    intermediate_layer = GraphQLError(message="Oink")
    graphql_error = GraphQLError(message="Meow")
    intermediate_layer.original_error = original_error
    graphql_error.original_error = intermediate_layer
    extracted_error = extract_original_error(graphql_error)
    assert extracted_error == original_error


def test_get_full_django_validation_error_details_plain_message():
    error = django.core.exceptions.ValidationError("meow")
    error_details = get_full_django_validation_error_details(error)
    assert error_details == {"non_field_errors": ["meow"]}


def test_get_full_django_validation_error_details_list_of_messages():
    error = django.core.exceptions.ValidationError(["meow", "woof"])
    error_details = get_full_django_validation_error_details(error)
    assert error_details == {"non_field_errors": ["meow", "woof"]}


def test_get_full_django_validation_error_details_dictionary():
    error = django.core.exceptions.ValidationError({"cat": "meow", "dog": "woof"})
    error_details = get_full_django_validation_error_details(error)
    assert error_details == {"cat": ["meow"], "dog": ["woof"]}


def test_format_graphql_error_no_original_error():
    graphql_error = GraphQLError(message="Meow")
    formatted_error_messaging = format_graphql_error(graphql_error)
    assert formatted_error_messaging == {
        "message": "Meow",
        "locations": None,
        "path": None,
    }


def test_format_graphql_error_django_validation_error():
    graphql_error = GraphQLError(message="Meow")
    validation_error = django.core.exceptions.ValidationError(
        {"cat": ["meow", "hiss"], "non_field_errors": ["oink"]}
    )
    graphql_error.original_error = validation_error
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "message": "Invalid input",
        "locations": None,
        "path": None,
        "state": {"cat": ["meow", "hiss"], "non_field_errors": ["oink"]},
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_rest_validation_error():
    graphql_error = GraphQLError(message="Meow")
    validation_error = rest_framework.exceptions.ValidationError(
        {"cat": ["meow", "hiss"], "non_field_errors": ["Test"]}
    )
    graphql_error.original_error = validation_error
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "locations": None,
        "message": "Invalid input",
        "path": None,
        "state": {
            "cat": [
                {
                    "code": "invalid",
                    "message": rest_framework.exceptions.ErrorDetail(
                        string="meow", code="invalid"
                    ),
                },
                {
                    "code": "invalid",
                    "message": rest_framework.exceptions.ErrorDetail(
                        string="hiss", code="invalid"
                    ),
                },
            ],
            "non_field_errors": [
                {
                    "code": "invalid",
                    "message": rest_framework.exceptions.ErrorDetail(
                        string="Test", code="invalid"
                    ),
                },
            ],
        },
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_authentication_error():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = rest_framework.exceptions.NotAuthenticated("")
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "locations": None,
        "message": "Unauthorized",
        "path": None,
        "state": {
            "non_field_errors": [
                "You are not currently authorized to make this request."
            ]
        },
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_object_does_not_exist_error():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = django.core.exceptions.ObjectDoesNotExist()
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "locations": None,
        "message": "Not found",
        "path": None,
        "state": {
            "non_field_errors": ["We were unable to locate the resource you requested."]
        },
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_django_permission_denied():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = django.core.exceptions.PermissionDenied()
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "locations": None,
        "message": "Forbidden",
        "path": None,
        "state": {
            "non_field_errors": ["You do not have permission to perform this action."]
        },
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_rest_permission_denied():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = rest_framework.exceptions.PermissionDenied("")
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "locations": None,
        "message": "Forbidden",
        "path": None,
        "state": {
            "non_field_errors": ["You do not have permission to perform this action."]
        },
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_multiple_objects_error():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = django.core.exceptions.MultipleObjectsReturned()
    formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {
        "locations": None,
        "message": "Multiple found",
        "path": None,
        "state": {
            "non_field_errors": [
                "Multiple resources were returned when only a single resource was expected"
            ]
        },
    }
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_validation_error_rest_framework_disabled():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = rest_framework.exceptions.ValidationError(
        {"cat": ["meow"]}
    )
    with mock.patch(
        "ariadne.contrib.django.format_error.is_rest_framework_enabled",
        return_value=False,
    ):
        formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {"message": "Meow", "locations": None, "path": None}
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_not_authenticated_rest_framework_disabled():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = rest_framework.exceptions.NotAuthenticated("")
    with mock.patch(
        "ariadne.contrib.django.format_error.is_rest_framework_enabled",
        return_value=False,
    ):
        formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {"message": "Meow", "locations": None, "path": None}
    assert formatted_error_messaging == expected_value


def test_format_graphql_error_permission_denied_rest_framework_disabled():
    graphql_error = GraphQLError(message="Meow")
    graphql_error.original_error = rest_framework.exceptions.PermissionDenied("")
    with mock.patch(
        "ariadne.contrib.django.format_error.is_rest_framework_enabled",
        return_value=False,
    ):
        formatted_error_messaging = format_graphql_error(graphql_error)
    expected_value = {"message": "Meow", "locations": None, "path": None}
    assert formatted_error_messaging == expected_value


def test_format_error_with_debug():
    graphql_error = GraphQLError(message="Meow")
    formatted_error_messaging = format_graphql_error(graphql_error, debug=True)
    assert formatted_error_messaging == {
        "message": "Meow",
        "locations": None,
        "path": None,
        "extensions": {"exception": None},
    }


def test_is_rest_framework_enabled():
    value = is_rest_framework_enabled()
    assert value
