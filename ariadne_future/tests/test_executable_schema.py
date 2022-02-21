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
