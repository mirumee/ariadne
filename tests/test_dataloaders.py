import sys
from unittest.mock import AsyncMock, Mock

import pytest
from aiodataloader import DataLoader as AsyncDataLoader

from ariadne import QueryType, graphql, graphql_sync, make_executable_schema

if sys.version_info > (3,7):
    # Sync dataloader is python 3.8 and later only
    from graphql_sync_dataloaders import DeferredExecutionContext, SyncDataLoader


@pytest.mark.asyncio
async def test_graphql_supports_async_dataloaders():
    type_defs = """
        type Query {
            test(arg: ID!): String!
        }
    """

    dataloader_fn = AsyncMock(side_effect=lambda keys: keys)
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
    dataloader_fn.assert_called_once_with(["1", "2"])


@pytest.mark.skipif(sys.version_info < (3,8), reason="requires python 3.8")
def test_graphql_sync_supports_sync_dataloaders():
    type_defs = """
        type Query {
            test(arg: ID!): String!
        }
    """

    dataloader_fn = Mock(side_effect=lambda keys: keys)
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
    dataloader_fn.assert_called_once_with(["1", "2"])
