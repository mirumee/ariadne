import pytest
from freezegun import freeze_time
from graphql import get_introspection_query

from ariadne import graphql_sync as graphql
from ariadne.contrib.tracing.apollotracing import (
    ApolloTracingExtensionSync as ApolloTracingExtension,
)


@pytest.mark.asyncio
async def test_apollotracing_extension_causes_no_errors_in_query_execution(schema):
    _, result = graphql(
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
async def test_apollotracing_extension_adds_tracing_data_to_result_extensions(
    schema, freeze_microtime, snapshot  # pylint: disable=unused-argument
):
    _, result = graphql(
        schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    snapshot.assert_match(result)


@freeze_time("2012-01-14 03:21:34")
@pytest.mark.asyncio
async def test_apollotracing_extension_handles_exceptions_in_resolvers(
    schema, freeze_microtime, snapshot  # pylint: disable=unused-argument
):
    _, result = graphql(
        schema, {"query": "{ testError }"}, extensions=[ApolloTracingExtension]
    )
    snapshot.assert_match(result["data"])


@pytest.mark.asyncio
async def test_apollotracing_extension_doesnt_break_introspection(schema):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = graphql(
        schema, {"query": introspection_query}, extensions=[ApolloTracingExtension]
    )
    assert "errors" not in result
