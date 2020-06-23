import sys
from typing import Dict, Any

import django.core.exceptions
from graphql import GraphQLError

try:
    import rest_framework.exceptions
except ImportError:
    pass

from ariadne import get_error_extension
from ariadne.contrib.django.constants import FORMATTED_ERROR_MESSAGES


def format_graphql_error(
    error: GraphQLError,
    error_field_name: str = "state",
    constants: Dict[str, Any] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    We do not want to render arcane for-developer-only errors in the same way
    we render user facing errors.  So, we should use a custom field for
    user-feedback related errors.  We will well established patterns and
    practices used by ValidationError in core django and django rest framework.
    Any non-form errors will also be rendered in non_field_errors.
    """
    if constants is None:
        constants = FORMATTED_ERROR_MESSAGES

    rest_framework_enabled = is_rest_framework_enabled()

    formatted = error.formatted
    original_error = extract_original_error(error)

    if isinstance(original_error, django.core.exceptions.ValidationError):
        formatted["message"] = constants["ValidationError"]["short"]
        formatted[error_field_name] = get_full_django_validation_error_details(
            original_error
        )

    elif rest_framework_enabled and isinstance(
        original_error, rest_framework.exceptions.ValidationError
    ):
        formatted["message"] = constants["ValidationError"]["short"]
        formatted[error_field_name] = original_error.get_full_details()

    elif isinstance(original_error, django.core.exceptions.ObjectDoesNotExist):
        formatted["message"] = constants["ObjectDoesNotExist"]["short"]
        formatted.setdefault(error_field_name, {})
        formatted[error_field_name].setdefault("non_field_errors", [])
        formatted[error_field_name]["non_field_errors"].append(
            constants["ObjectDoesNotExist"]["details"]
        )

    elif rest_framework_enabled and isinstance(
        original_error, rest_framework.exceptions.NotAuthenticated
    ):
        formatted["message"] = constants["NotAuthenticated"]["short"]
        formatted.setdefault(error_field_name, {})
        formatted[error_field_name].setdefault("non_field_errors", [])
        formatted[error_field_name]["non_field_errors"].append(
            constants["NotAuthenticated"]["details"]
        )

    elif any(
        [
            isinstance(original_error, django.core.exceptions.PermissionDenied),
            rest_framework_enabled
            and isinstance(original_error, rest_framework.exceptions.PermissionDenied),
        ]
    ):
        formatted["message"] = constants["PermissionDenied"]["short"]
        formatted.setdefault(error_field_name, {})
        formatted[error_field_name].setdefault("non_field_errors", [])
        formatted[error_field_name]["non_field_errors"].append(
            constants["PermissionDenied"]["details"]
        )

    elif isinstance(original_error, django.core.exceptions.MultipleObjectsReturned):
        formatted["message"] = constants["MultipleObjectsReturned"]["short"]
        formatted.setdefault(error_field_name, {})
        formatted[error_field_name].setdefault("non_field_errors", [])
        formatted[error_field_name]["non_field_errors"].append(
            constants["MultipleObjectsReturned"]["details"]
        )

    if debug:
        formatted.setdefault("extensions", {})
        formatted["extensions"]["exception"] = get_error_extension(error)
    return formatted


def extract_original_error(error: GraphQLError):
    # Sometimes, ariadne nests the originally raised error.  So, get to the bottom of it!
    while getattr(error, "original_error", None):
        error = error.original_error
    return error


def get_full_django_validation_error_details(
    error: django.core.exceptions.ValidationError,
) -> Dict[str, Any]:
    if getattr(error, "message_dict", None) is not None:
        result = error.message_dict
    elif getattr(error, "message", None) is not None:
        result = {"non_field_errors": [error.message]}
    else:
        result = {"non_field_errors": error.messages}
    return result


def is_rest_framework_enabled() -> bool:
    return "rest_framework.exceptions" in sys.modules
