from collections import defaultdict
from statistics import mean
from time import time
from inspect import iscoroutinefunction

from graphql.pyutils import is_awaitable
from starlette.testclient import TestClient

from ariadne import gql
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.types import Extension, ExtensionSync

from .schema import schema

TEST_QUERY = gql(
    """
    query GetThreads {
        threads {
            id
            category {
                id
                name
                slug
                color
                parent {
                    id
                    name
                    slug
                    color
                }
            }
            title
            slug
            starter {
                id
                handle
                slug
                name
                title
                group {
                    title
                }
            }
            starterName
            startedAt
            lastPoster {
                id
                handle
                slug
                name
                title
                group {
                    title
                }
            }
            lastPosterName
            lastPostedAt
            isClosed
            isHidden
            replies {
                ... ReplyData
                replies {
                    ... ReplyData
                }
            }
        }
    }

    fragment ReplyData on Post {
        id
        poster {
            id
            handle
            slug
            name
            title
            group {
                title
            }
        }
        postedAt
        content
        edits
    }
    """
)


def test_query_without_extensions(benchmark):
    app = GraphQL(schema)
    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": TEST_QUERY,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == 200
    assert not result.json().get("errors")


class NoopExtension(Extension):
    pass


def test_query_with_extension(benchmark):
    app = GraphQL(
        schema, http_handler=GraphQLHTTPHandler(extensions=[NoopExtension])
    )

    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": TEST_QUERY,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == 200
    assert not result.json().get("errors")


class NoopExtensionSync(ExtensionSync):
    pass


def test_query_with_extension_sync(benchmark):
    app = GraphQL(
        schema, http_handler=GraphQLHTTPHandler(extensions=[NoopExtensionSync])
    )

    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": TEST_QUERY,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == 200
    assert not result.json().get("errors")
