from ariadne.constants import HTTP_STATUS_200_OK

playground_response_headers = [("Content-Type", "text/html; charset=UTF-8")]


def test_playground_html_is_served_on_get_request(
    middleware, middleware_request, snapshot, start_response
):
    middleware_request["REQUEST_METHOD"] = "GET"
    response = middleware(middleware_request, start_response)
    start_response.assert_called_once_with(
        HTTP_STATUS_200_OK, playground_response_headers
    )
    snapshot.assert_match(response)
