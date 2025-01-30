import pytest
from aiodataloader import DataLoader as AsyncDataLoader
from graphql_sync_dataloaders import DeferredExecutionContext, SyncDataLoader

from ariadne import QueryType, graphql, graphql_sync, make_executable_schema


@pytest.mark.asyncio
async def test_graphql_supports_async_dataloaders():
    type_defs = """
        type Query {
            test(arg: ID!): String!
        }
    """

    async def dataloader_fn(keys):
        return keys

    dataloader = AsyncDataLoader(dataloader_fn)

    query = QueryType()
    query.set_field("test", lambda *_, arg: dataloader.load(arg))

    schema = make_executable_schema(
        type_defs,
        [query],
    )

    success, result = await graphql(
        schema,
        {"query": "{ test1: test(arg: 1), test2: test(arg: 2) }"},
    )
    assert success
    assert result["data"] == {"test1": "1", "test2": "2"}


def test_graphql_sync_supports_sync_dataloaders():
    type_defs = """
        type Query {
            test(arg: ID!): String!
        }
    """

    def dataloader_fn(keys):
        return keys

    dataloader = SyncDataLoader(dataloader_fn)

    query = QueryType()
    query.set_field("test", lambda *_, arg: dataloader.load(arg))

    schema = make_executable_schema(
        type_defs,
        [query],
    )

    success, result = graphql_sync(
        schema,
        {"query": "{ test1: test(arg: 1), test2: test(arg: 2) }"},
        execution_context_class=DeferredExecutionContext,
    )
    assert success
    assert result["data"] == {"test1": "1", "test2": "2"}
