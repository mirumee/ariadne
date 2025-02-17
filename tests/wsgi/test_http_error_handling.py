from unittest.mock import Mock

from ariadne.constants import HttpStatusResponse
from ariadne.exceptions import HttpBadRequestError, HttpError


def test_http_errors_raised_in_handle_request_are_passed_to_http_error_handler(
    middleware, middleware_request, start_response
):
    exception = HttpError(status=HttpStatusResponse.METHOD_NOT_ALLOWED.value)
    middleware.graphql_app.handle_request = Mock(side_effect=exception)
    handle_error = middleware.graphql_app.handle_http_error = Mock()
    middleware(middleware_request, start_response)

    handle_error.assert_called_once_with(exception, start_response)


def test_http_error_400_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response, error_response_headers
):
    exception = HttpBadRequestError()
    middleware.graphql_app.handle_request = Mock(side_effect=exception)

    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [str(exception.status).encode("utf-8")]


def test_http_error_400_with_message_is_converted_to_http_response_in_http_error_handler(  #  noqa: E501
    middleware, middleware_request, start_response, error_response_headers
):
    message = "This is bad request error."
    exception = HttpBadRequestError(message)
    middleware.graphql_app.handle_request = Mock(side_effect=exception)

    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [message.encode("utf-8")]
