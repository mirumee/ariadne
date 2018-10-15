import pytest

from ariadne import GraphQLMiddleware


class CustomGraphQLMiddleware(GraphQLMiddleware):
    def get_query_root(self, environ, request_data):
        """Override this method in inheriting class to create query root."""
        return {"user": {"id": None, "username": "Anonymous"}}

    def get_query_context(self, environ, request_data):
        """Override this method in inheriting class to create query context."""
        return {"environ": environ, "has_valid_auth": True}


type_defs = """
type Query {
    hasValidAuth: Boolean!
    user: Boolean!
}
"""


def resolve_has_valid_auth(_, info):
    return info.context["has_valid_auth"]


def resolve_user(parent, _):
    return parent["user"]


resolvers = {"Query": {"hasValidAuth": resolve_has_valid_auth, "user": resolve_user}}


@pytest.fixture
def custom_middleware(app_mock):
    return CustomGraphQLMiddleware(app_mock, type_defs, resolvers)


def test_custom_middleware_executes_query_with_custom_query_context(
    custom_middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(query="{ hasValidAuth }")
    result = custom_middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    assert_json_response_equals_snapshot(result)


def test_custom_middleware_executes_query_with_custom_query_root(
    custom_middleware,
    start_response,
    graphql_query_request_factory,
    graphql_response_headers,
    assert_json_response_equals_snapshot,
):
    request = graphql_query_request_factory(query="{ user }")
    result = custom_middleware(request, start_response)
    start_response.assert_called_once_with("200 OK", graphql_response_headers)
    assert_json_response_equals_snapshot(result)
