from typing import List

from graphql import parse

from .schema import Schema


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


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)
