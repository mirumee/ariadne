import pytest
from graphql import ExecutionContext, GraphQLError
from graphql.validation.rules import ValidationRule

from ariadne import graphql, graphql_sync, subscribe


class AlwaysInvalid(ValidationRule):
    def leave_operation_definition(  # pylint: disable=unused-argument
        self, *args, **kwargs
    ):
        self.context.report_error(GraphQLError("Invalid"))


def test_graphql_sync_executes_the_query(schema):
    success, result = graphql_sync(schema, {"query": '{ hello(name: "world") }'})
    assert success
    assert result["data"] == {"hello": "Hello, world!"}


def test_graphql_sync_uses_validation_rules(schema):
    success, result = graphql_sync(
        schema, {"query": '{ hello(name: "world") }'}, validation_rules=[AlwaysInvalid]
    )
    assert not success
    assert result["errors"][0]["message"] == "Invalid"


def test_graphql_sync_uses_execution_context_class(schema):
    class TestExecutionContext(ExecutionContext):
        def execute_field(self, *_):
            return "test"

    success, result = graphql_sync(
        schema,
        {"query": '{ hello(name: "world") }'},
        execution_context_class=TestExecutionContext,
    )
    assert success
    assert result["data"] == {"hello": "test"}


def test_graphql_sync_prevents_introspection_query_when_option_is_disabled(schema):
    success, result = graphql_sync(
        schema, {"query": "{ __schema { types { name } } }"}, introspection=False
    )
    assert not success
    assert (
        result["errors"][0]["message"]
        == "Cannot query '__schema': introspection is disabled."
    )


@pytest.mark.asyncio
async def test_graphql_execute_the_query(schema):
    success, result = await graphql(schema, {"query": '{ hello(name: "world") }'})
    assert success
    assert result["data"] == {"hello": "Hello, world!"}


@pytest.mark.asyncio
async def test_graphql_uses_validation_rules(schema):
    success, result = await graphql(
        schema, {"query": '{ hello(name: "world") }'}, validation_rules=[AlwaysInvalid]
    )
    assert not success
    assert result["errors"][0]["message"] == "Invalid"


@pytest.mark.asyncio
async def test_graphql_uses_execution_context_class(schema):
    class TestExecutionContext(ExecutionContext):
        def execute_field(self, *_):
            return "test"

    success, result = await graphql(
        schema,
        {"query": '{ hello(name: "world") }'},
        execution_context_class=TestExecutionContext,
    )
    assert success
    assert result["data"] == {"hello": "test"}


@pytest.mark.asyncio
async def test_graphql_prevents_introspection_query_when_option_is_disabled(schema):
    success, result = await graphql(
        schema, {"query": "{ __schema { types { name } } }"}, introspection=False
    )
    assert not success
    assert (
        result["errors"][0]["message"]
        == "Cannot query '__schema': introspection is disabled."
    )


@pytest.mark.asyncio
async def test_subscription_returns_an_async_iterator(schema):
    success, result = await subscribe(schema, {"query": "subscription { ping }"})
    assert success
    # next() doesn't work async and anext is py>=3.10
    response = await result.__anext__()  # pylint: disable=unnecessary-dunder-call
    assert response.data == {"ping": "pong"}


@pytest.mark.asyncio
async def test_subscription_uses_validation_rules(schema):
    success, result = await subscribe(
        schema, {"query": "subscription { ping }"}, validation_rules=[AlwaysInvalid]
    )
    assert not success
    assert result[0]["message"] == "Invalid"


@pytest.mark.asyncio
async def test_subscription_prevents_introspection_query_when_option_is_disabled(
    schema,
):
    success, result = await subscribe(
        schema, {"query": "{ __schema { types { name } } }"}, introspection=False
    )
    assert not success
    assert result[0]["message"] == "Cannot query '__schema': introspection is disabled."
