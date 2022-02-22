import pytest
from graphql import graphql_sync

from ..executable_schema import make_executable_schema
from ..object_type import ObjectType


def test_executable_schema_is_created_from_object_types():
    class UserType(ObjectType):
        __schema__ = """
        type User {
            id: ID!
            username: String!
        }
        """
        __resolvers__ = {
            "username": "user_name",
        }

    class QueryType(ObjectType):
        __schema__ = """
        type Query {
            user: User
        }
        """
        __requires__ = [UserType]

        @staticmethod
        def user(*_):
            return {
                "id": 1,
                "user_name": "Alice",
            }

    schema = make_executable_schema(QueryType)
    result = graphql_sync(schema, "{ user { id username } }")
    assert result.errors is None
    assert result.data == {"user": {"id": "1", "username": "Alice"}}


def test_executable_schema_merges_root_types():
    class CityQueryType(ObjectType):
        __schema__ = """
        type Query {
            city: String!
        }
        """

        @staticmethod
        def city(*_):
            return "Wroclaw"

    class YearQueryType(ObjectType):
        __schema__ = """
        type Query {
            year: Int!
        }
        """

        @staticmethod
        def year(*_):
            return 2022

    schema = make_executable_schema(CityQueryType, YearQueryType)
    result = graphql_sync(schema, "{ city, year }")
    assert result.errors is None
    assert result.data == {"city": "Wroclaw", "year": 2022}


def test_executable_schema_raises_value_error_if_merged_types_define_same_field(
    snapshot,
):
    class CityQueryType(ObjectType):
        __schema__ = """
        type Query {
            city: String!
        }
        """

        @staticmethod
        def city(*_):
            return "Wroclaw"

    class YearQueryType(ObjectType):
        __schema__ = """
        type Query {
            city: String!
            year: Int!
        }
        """

        @staticmethod
        def year(*_):
            return 2022

    with pytest.raises(ValueError) as err:
        make_executable_schema(CityQueryType, YearQueryType)

    snapshot.assert_match(err)
