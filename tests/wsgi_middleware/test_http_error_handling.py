from unittest.mock import Mock

from ariadne.exceptions import HttpError, HttpBadRequestError, HttpMethodNotAllowedError


def test_http_errors_raised_in_handle_request_are_passed_to_http_error_handler(
    middleware, middleware_request, start_response
):
    exception = HttpError()
    middleware.handle_request = Mock(side_effect=exception)
    middleware.handle_http_error = Mock(return_value=[])
    list(middleware(middleware_request, start_response))

    middleware.handle_http_error.assert_called_once_with(exception, start_response)


def test_http_error_400_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response, error_response_headers
):
    exception = HttpBadRequestError()
    middleware.handle_request = Mock(side_effect=exception)

    response = list(middleware(middleware_request, start_response))
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [exception.status.encode("utf-8")]


def test_http_error_400_with_message_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response, error_response_headers
):
    message = "This is bad request error."
    exception = HttpBadRequestError(message)
    middleware.handle_request = Mock(side_effect=exception)

    response = list(middleware(middleware_request, start_response))
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [message.encode("utf-8")]


def test_http_error_405_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response, error_response_headers
):
    exception = HttpMethodNotAllowedError()
    middleware.handle_request = Mock(side_effect=exception)

    response = list(middleware(middleware_request, start_response))
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [exception.status.encode("utf-8")]


def test_http_error_405_with_message_is_converted_to_http_response_in_http_error_handler(
    middleware, middleware_request, start_response, error_response_headers
):
    message = "This is method not allowed error."
    exception = HttpMethodNotAllowedError(message)
    middleware.handle_request = Mock(side_effect=exception)

    response = list(middleware(middleware_request, start_response))
    start_response.assert_called_once_with(exception.status, error_response_headers)
    assert response == [message.encode("utf-8")]
