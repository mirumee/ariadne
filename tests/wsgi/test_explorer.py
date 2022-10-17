from ariadne.explorer import (
    ExplorerApollo,
    ExplorerGraphiQL,
    ExplorerHttp405,
    ExplorerPlayground,
)
from ariadne.constants import HTTP_STATUS_200_OK, HTTP_STATUS_405_METHOD_NOT_ALLOWED

playground_response_headers = [("Content-Type", "text/html; charset=UTF-8")]


def test_default_explorer_html_is_served_on_get_request(
    middleware, middleware_request, snapshot, start_response
):
    middleware_request["REQUEST_METHOD"] = "GET"
    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HTTP_STATUS_200_OK, playground_response_headers
    )
    snapshot.assert_match(response)


def test_apollo_html_is_served_on_get_request(
    server, middleware, middleware_request, snapshot, start_response
):
    server.explorer = ExplorerApollo()
    middleware_request["REQUEST_METHOD"] = "GET"
    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HTTP_STATUS_200_OK, playground_response_headers
    )
    snapshot.assert_match(response)


def test_graphiql_html_is_served_on_get_request(
    server, middleware, middleware_request, snapshot, start_response
):
    server.explorer = ExplorerGraphiQL()
    middleware_request["REQUEST_METHOD"] = "GET"
    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HTTP_STATUS_200_OK, playground_response_headers
    )
    snapshot.assert_match(response)


def test_playground_html_is_served_on_get_request(
    server, middleware, middleware_request, snapshot, start_response
):
    server.explorer = ExplorerPlayground()
    middleware_request["REQUEST_METHOD"] = "GET"
    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HTTP_STATUS_200_OK, playground_response_headers
    )
    snapshot.assert_match(response)


def test_405_bad_method_is_served_on_get_request_for_disabled_explorer(
    server, middleware, middleware_request, snapshot, start_response
):
    server.explorer = ExplorerHttp405()
    middleware_request["REQUEST_METHOD"] = "GET"
    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HTTP_STATUS_405_METHOD_NOT_ALLOWED,
        [
            ("Content-Type", "text/plain; charset=UTF-8"),
            ("Content-Length", 0),
            ("Allow", "OPTIONS, POST, GET"),
        ],
    )
    snapshot.assert_match(response)
