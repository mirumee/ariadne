# pylint: disable=too-many-arguments, too-complex

import json
from io import StringIO
from unittest.mock import Mock

import pytest

from ariadne import GraphQLMiddleware


@pytest.fixture
def type_defs():
    return """
        type Query {
            hello(name: String): String
            status: Boolean
        }
    """


def resolve_hello(*_, name):
    return "Hello, %s!" % name


def resolve_status(*_):
    return True


@pytest.fixture
def resolvers():
    return {"Query": {"hello": resolve_hello, "status": resolve_status}}


@pytest.fixture
def graphql_response_headers():
    return [("Content-Type", "application/json; charset=UTF-8")]


@pytest.fixture
def error_response_headers():
    return [("Content-Type", "text/plain; charset=UTF-8")]


@pytest.fixture
def failed_query_http_status():
    return "400 Bad Request"


@pytest.fixture
def app_mock():
    return Mock(return_value=True)


@pytest.fixture
def start_response():
    return Mock()


@pytest.fixture
def middleware(app_mock, type_defs, resolvers):
    return GraphQLMiddleware(app_mock, type_defs=type_defs, resolvers=resolvers)


@pytest.fixture
def server(type_defs, resolvers):
    return GraphQLMiddleware(None, type_defs=type_defs, resolvers=resolvers, path="/")


@pytest.fixture
def middleware_request():
    return {"PATH_INFO": "/graphql/"}


@pytest.fixture
def graphql_query_request_factory(middleware_request):
    def wrapped_graphql_query_request_factory(
        raw_data=None,
        query=None,
        operationName=None,
        variables=None,
        content_type="application/json",
        content_length=None,
    ):
        data = {}
        if query:
            data["query"] = query
        if operationName:
            data["operationName"] = operationName
        if variables:
            data["variables"] = variables
        data_json = json.dumps(data)

        middleware_request.update(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": content_length or len(data_json),
                "wsgi.input": StringIO(data_json if data else ""),
            }
        )

        if raw_data:
            middleware_request.update(
                {
                    "CONTENT_LENGTH": content_length or len(raw_data),
                    "wsgi.input": StringIO(raw_data),
                }
            )

        return middleware_request

    return wrapped_graphql_query_request_factory


@pytest.fixture
def assert_json_response_equals_snapshot(snapshot):
    def assertion(reponse):
        deserialized_data = json.loads(reponse[0].decode("utf-8"))
        snapshot.assert_match(deserialized_data)

    return assertion
