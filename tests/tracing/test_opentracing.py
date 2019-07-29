import pytest

from ariadne import graphql
from ariadne.contrib.tracing.opentracing import (
    OpenTracingExtension,
    opentracing_extension,
)


@pytest.mark.asyncio
async def test_opentracing_extension_causes_no_errors_in_query_execution(schema):
    _, result = await graphql(
        schema,
        {"query": '{ status hello(name:"bob") }'},
        extensions=[OpenTracingExtension],
    )
    assert result == {"data": {"hello": "Hello, bob!", "status": True}}
