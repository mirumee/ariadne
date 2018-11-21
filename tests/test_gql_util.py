import pytest
from graphql.error import GraphQLSyntaxError

from ariadne import gql


def test_valid_graphql_schema_string_is_returned_unchanged():
    sdl = """
        type User {
            username: String!
        }
    """
    result = gql(sdl)
    assert sdl == result


def test_invalid_graphql_schema_string_causes_syntax_error():
    with pytest.raises(GraphQLSyntaxError):
        gql(
            """
                type User {
                    username String!
                }
            """
        )


def test_valid_graphql_query_string_is_returned_unchanged():
    query = """
        query TestQuery {
            auth
            users {
                id
                username
            }
        }
    """
    result = gql(query)
    assert query == result


def test_invalid_graphql_query_string_causes_syntax_error():
    with pytest.raises(GraphQLSyntaxError):
        gql(
            """
                query TestQuery {
                    auth
                    users
                        id
                        username
                    }
                }
            """
        )
