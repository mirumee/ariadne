import json
from io import StringIO
from unittest.mock import Mock

import pytest
from werkzeug.test import Client

from ariadne.wsgi import GraphQL, GraphQLMiddleware


@pytest.fixture
def client(app):
    return Client(app)


@pytest.fixture
def graphql_response_headers():
    return [("Content-Type", "application/json; charset=UTF-8")]


@pytest.fixture
def error_response_headers():
    return [("Content-Type", "text/plain; charset=UTF-8")]


@pytest.fixture
def app_mock():
    return Mock(return_value=True)


@pytest.fixture
def start_response():
    return Mock()


@pytest.fixture
def server(schema):
    return GraphQL(schema)


@pytest.fixture
def middleware(app_mock, server):
    return GraphQLMiddleware(app_mock, server)


@pytest.fixture
def middleware_request():
    return {"PATH_INFO": "/graphql/"}


@pytest.fixture
def graphql_query_request_factory(middleware_request):
    def wrapped_graphql_query_request_factory(
        raw_data=None,
        query=None,
        operation_name=None,
        variables=None,
        content_type="application/json",
        content_length=None,
    ):
        data = {}
        if query:
            data["query"] = query
        if operation_name:
            data["operationName"] = operation_name
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
        assert snapshot == deserialized_data

    return assertion
