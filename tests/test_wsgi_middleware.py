from unittest.mock import Mock

import pytest

from ariadne import GraphQLMiddleware

type_defs = """
    type Query {
        test: String
    }
"""


@pytest.fixture
def app_mock():
    return Mock(return_value=True)


@pytest.fixture
def graphql_middleware(app_mock):
    return GraphQLMiddleware(
        app_mock, type_defs=type_defs, resolvers={}, path="/graphql/"
    )


def test_middleware_dispatches_request_to_wrapped_app(app_mock, graphql_middleware):
    graphql_middleware({"PATH_INFO": "/"}, Mock())
    assert app_mock.called


def test_middleware_dispatches_request_to_graphql(app_mock, graphql_middleware):
    graphql_middleware.serve_request = Mock()
    graphql_middleware({"PATH_INFO": "/graphql/", "REQUEST_METHOD": "GET"}, Mock())
    assert graphql_middleware.serve_request.called
    assert not app_mock.called
