import pytest
from graphql import get_introspection_query

from ariadne import graphql
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension


@pytest.mark.asyncio
async def test_apollotracing_extension_causes_no_errors_in_query_execution(schema):
    _, result = await graphql(
        schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    assert result["data"] == {"status": True}


@pytest.mark.asyncio
async def test_apollotracing_extension_adds_tracing_data_to_result_extensions(schema):
    _, result = await graphql(
        schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )
    assert result["extensions"]["tracing"]["version"] == 1
    assert result["extensions"]["tracing"]["startTime"]
    assert result["extensions"]["tracing"]["endTime"]
    assert result["extensions"]["tracing"]["duration"]
    assert result["extensions"]["tracing"]["execution"]


@pytest.mark.asyncio
async def test_apollotracing_extension_adds_resolvers_timing_in_result_extensions(
    schema
):
    _, result = await graphql(
        schema, {"query": "{ status }"}, extensions=[ApolloTracingExtension]
    )

    resolvers = result["extensions"]["tracing"]["execution"]["resolvers"]

    assert len(resolvers) == 1
    assert resolvers[0]["path"] == ["status"]
    assert resolvers[0]["parentType"] == "Query"
    assert resolvers[0]["fieldName"] == "status"
    assert resolvers[0]["returnType"] == "Boolean"
    assert resolvers[0]["startOffset"]
    assert resolvers[0]["duration"]


@pytest.mark.asyncio
async def test_apollotracing_extension_handles_exceptions_in_resolvers(schema):
    _, result = await graphql(
        schema, {"query": "{ testError }"}, extensions=[ApolloTracingExtension]
    )

    resolvers = result["extensions"]["tracing"]["execution"]["resolvers"]

    assert len(resolvers) == 1
    assert resolvers[0]["path"] == ["testError"]
    assert resolvers[0]["parentType"] == "Query"
    assert resolvers[0]["fieldName"] == "testError"
    assert resolvers[0]["returnType"] == "Boolean"
    assert resolvers[0]["startOffset"]
    assert resolvers[0]["duration"]


@pytest.mark.asyncio
async def test_apollotracing_extension_doesnt_break_introspection(schema):
    introspection_query = get_introspection_query(descriptions=True)
    _, result = await graphql(
        schema, {"query": introspection_query}, extensions=[ApolloTracingExtension]
    )
    assert "errors" not in result
