from typing import Optional, Union

from graphql import GraphQLError, parse


def convert_camel_case_to_snake(graphql_name: str) -> str:
    python_name = ""
    for i, c in enumerate(graphql_name.lower()):
        if i and c != graphql_name[i]:
            python_name += "_"
        python_name += c
    return python_name


def gql(value: str) -> str:
    parse(value)
    return value


def unwrap_graphql_error(
    error: Union[GraphQLError, Optional[Exception]]
) -> Optional[Exception]:
    if isinstance(error, GraphQLError):
        return unwrap_graphql_error(error.original_error)
    return error
