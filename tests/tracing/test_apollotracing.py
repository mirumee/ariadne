import pytest
from freezegun import freeze_time
from graphql import get_introspection_query

from ariadne import graphql, graphql_sync
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension


@pytest.mark.asyncio
async def test_apollotracing_extension_causes_no_errors_in_async_query_execution(
    async_schema,
):
    _, result = await graphql(
        async_schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    assert result["data"] == {"status": True}


def test_apollotracing_extension_causes_no_errors_in_sync_query_execution(schema):
    _, result = graphql_sync(
        schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    assert result["data"] == {"status": True}


@pytest.fixture
def freeze_microtime(mocker):
    mocker.patch(
        "ariadne.contrib.tracing.apollotracing.perf_counter_ns", return_value=2
    )


@freeze_time("2012-01-14 03:21:34")
@pytest.mark.asyncio
async def test_apollotracing_extension_adds_tracing_data_to_async_result_extensions(
    async_schema,
    freeze_microtime,
    snapshot,
):
    _, result = await graphql(
        async_schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    assert snapshot == result


@freeze_time("2012-01-14 03:21:34")
def test_apollotracing_extension_adds_tracing_data_to_sync_result_extensions(
    schema,
    freeze_microtime,
    snapshot,
):
    _, result = graphql_sync(
        schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    assert snapshot == result


@freeze_time("2012-01-14 03:21:34")
@pytest.mark.asyncio
async def test_apollotracing_extension_handles_exceptions_in_resolvers_in_async_context(
    async_schema,
    freeze_microtime,
    snapshot,
):
    _, result = await graphql(
        async_schema, {"query": "{ testError }"}, extensions=[ApolloTracingExtension]
    )
    assert snapshot == result["data"]


@freeze_time("2012-01-14 03:21:34")
def test_apollotracing_extension_handles_exceptions_in_resolvers_in_sync_context(
    schema,
    freeze_microtime,
    snapshot,
):
    _, result = graphql_sync(
        schema, {"query": "{ testError }"}, extensions=[ApolloTracingExtension]
    )
    assert snapshot == result["data"]


@pytest.mark.asyncio
async def test_apollotracing_extension_doesnt_break_introspection_in_async_context(
    async_schema,
):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = await graphql(
        async_schema,
        {"query": introspection_query},
        extensions=[ApolloTracingExtension],
    )
    assert "errors" not in result


def test_apollotracing_extension_doesnt_break_introspection_in_sync_context(schema):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = graphql_sync(
        schema, {"query": introspection_query}, extensions=[ApolloTracingExtension]
    )
    assert "errors" not in result
