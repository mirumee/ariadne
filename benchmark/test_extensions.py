from http import HTTPStatus

from starlette.testclient import TestClient

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.opentelemetry import OpenTelemetryExtension
from ariadne.contrib.tracing.opentracing import OpenTracingExtension
from ariadne.types import Extension

from .schema import schema


def test_query_without_extensions(benchmark, benchmark_query):
    app = GraphQL(schema)
    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": benchmark_query,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == HTTPStatus.OK
    assert not result.json().get("errors")


def test_query_with_noop_extension(benchmark, benchmark_query):
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(extensions=[Extension]),
    )

    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": benchmark_query,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == HTTPStatus.OK
    assert not result.json().get("errors")


def test_query_with_open_telemetry_extension(benchmark, benchmark_query):
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(extensions=[OpenTelemetryExtension]),
    )

    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": benchmark_query,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == HTTPStatus.OK
    assert not result.json().get("errors")


def test_query_with_open_tracing_extension(benchmark, benchmark_query):
    app = GraphQL(
        schema,
        http_handler=GraphQLHTTPHandler(extensions=[OpenTracingExtension]),
    )

    client = TestClient(app)

    def api_call():
        return client.post(
            "/",
            json={
                "operationName": "GetThreads",
                "query": benchmark_query,
            },
        )

    result = benchmark(api_call)
    assert result.status_code == HTTPStatus.OK
    assert not result.json().get("errors")
