import pytest

from graphql import graphql, graphql_sync

from ariadne import QueryType, make_executable_schema, map_kwargs


type_defs = """
    type Query {
        test(id: Int!, type: String, name: String): Boolean
    }
"""


def test_decorator_map_kwargs_sync():
    query = QueryType()

    @query.field("test")
    @map_kwargs({"id": "id_", "type": "user_type"})
    def resolve_test(*_, id_, user_type, name=None):  # pylint: disable=unused-variable
        assert id_ == 42
        assert user_type == "test"
        assert name == "untouched"

        return True

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, '{ test(id: 42, type: "test", name: "untouched") }')
    assert result.errors is None
    assert result.data == {"test": True}


@pytest.mark.asyncio
async def test_decorator_map_kwargs_async():
    query = QueryType()

    @query.field("test")
    @map_kwargs({"id": "id_", "type": "user_type"})
    async def resolve_test(
        *_, id_, user_type, name=None
    ):  # pylint: disable=unused-variable
        assert id_ == 42
        assert user_type == "test"
        assert name == "untouched"

        return True

    schema = make_executable_schema(type_defs, query)

    result = await graphql(schema, '{ test(id: 42, type: "test", name: "untouched") }')
    assert result.errors is None
    assert result.data == {"test": True}
