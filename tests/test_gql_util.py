import pytest
from graphql.error import GraphQLSyntaxError

from ariadne import gql


def test_valid_graphqll_string_is_passed_as_is():
    sdl = """
        type User {
            username: String!
        }
    """
    result = gql(sdl)
    assert sdl == result


def test_invalid_graphql_string_raises_syntax_error():
    with pytest.raises(GraphQLSyntaxError):
        gql(
            """
                type User {
                    username String!
                }
            """
        )
