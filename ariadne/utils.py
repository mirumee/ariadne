from graphql import parse


def gql(value: str) -> str:
    parse(value)
    return value
