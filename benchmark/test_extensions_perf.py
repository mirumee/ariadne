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


def test_benchmark_query_without_extensions(benchmark):
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


def format_timings(timings):
    formatted = {}

    for path, times in timings.items():
        formatted[path] = {
            "min": min(times),
            "mean": mean(times),
            "max": max(times),
        }

    return {"timings": formatted}


class TimingExtensionAsync(Extension):
    def __init__(self, *args, **kwargs):
        self._checks_cache = {}
        self._timings = defaultdict(list)

        super().__init__(*args, **kwargs)

    async def resolve(
        self,
        next_,
        obj,
        info,
        **kwargs,
    ):
        path = ".".join(map(str, info.path.as_list()))
        if path not in self._timings:
            self._timings[path] = []

        start = time()
        result = next_(obj, info, **kwargs)
        if is_awaitable(result):
            result = await result
        if is_awaitable(result):
            result = await result
        self._timings[path].append(time() - start)
        return result

    def format(self, context):
        return format_timings(self._timings)


def test_benchmark_query_with_async_extension(benchmark):
    app = GraphQL(
        schema, http_handler=GraphQLHTTPHandler(extensions=[TimingExtensionAsync])
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
    assert result.json().get("extensions")


class TimingExtensionSync(ExtensionSync):
    def __init__(self, *args, **kwargs):
        self._checks_cache = {}
        self._timings = defaultdict(list)

        super().__init__(*args, **kwargs)

    def resolve(
        self,
        next_,
        obj,
        info,
        **kwargs,
    ):
        path = ".".join(map(str, info.path.as_list()))
        if path not in self._timings:
            self._timings[path] = []

        path_hash = hash(path)
        if path_hash not in self._checks_cache:
            field_resolver = info.parent_type.fields[info.field_name].resolve
            if field_resolver:
                self._checks_cache[path_hash] = iscoroutinefunction(field_resolver)
            else:
                self._checks_cache[path_hash] = False

        if self._checks_cache[path_hash]:

            async def timeit_closure():
                start = time()
                result = await next_(obj, info, **kwargs)
                if is_awaitable(result):
                    result = await result
                self._timings[path].append(time() - start)
                return result

            return timeit_closure()

        start = time()
        result = next_(obj, info, **kwargs)
        self._timings[path].append(time() - start)

        return result

    def format(self, context):
        return format_timings(self._timings)


def test_benchmark_query_with_new_extension_caching(benchmark):
    app = GraphQL(
        schema, http_handler=GraphQLHTTPHandler(extensions=[TimingExtensionSync])
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
    assert result.json().get("extensions")


class TimingExtensionSyncNoCache(ExtensionSync):
    def __init__(self, *args, **kwargs):
        self._timings = defaultdict(list)

        super().__init__(*args, **kwargs)

    def resolve(
        self,
        next_,
        obj,
        info,
        **kwargs,
    ):
        path = ".".join(map(str, info.path.as_list()))
        if path not in self._timings:
            self._timings[path] = []

        field_resolver = info.parent_type.fields[info.field_name].resolve
        if field_resolver:
            is_async = iscoroutinefunction(field_resolver)
        else:
            is_async = False

        if is_async:

            async def timeit_closure():
                start = time()
                result = await next_(obj, info, **kwargs)
                if is_awaitable(result):
                    result = await result
                self._timings[path].append(time() - start)
                return result

            return timeit_closure()

        start = time()
        result = next_(obj, info, **kwargs)
        self._timings[path].append(time() - start)

        return result

    def format(self, context):
        return format_timings(self._timings)


def test_benchmark_query_with_new_extension_no_cache(benchmark):
    app = GraphQL(
        schema, http_handler=GraphQLHTTPHandler(extensions=[TimingExtensionSyncNoCache])
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
    assert result.json().get("extensions")
