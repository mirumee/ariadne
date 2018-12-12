import os
from typing import Generator

from graphql import parse
from graphql.error import GraphQLSyntaxError

from .exceptions import GraphQLFileSyntaxError


def load_schema_from_path(path: str) -> str:
    if os.path.isdir(path):
        schema_list = [read_graphql_file(f) for f in walk_graphql_files(path)]
        return "\n".join(schema_list)
    return read_graphql_file(os.path.abspath(path))


def walk_graphql_files(path: str) -> Generator:
    def abs_path(f):
        return os.path.abspath(os.path.join(path, f))

    return (abs_path(f) for f in sorted(os.listdir(path)) if f.endswith(".graphql"))


def read_graphql_file(path: str) -> str:
    with open(path, "r") as graphql_file:
        schema = graphql_file.read()
    try:
        parse(schema)
    except GraphQLSyntaxError as e:
        raise GraphQLFileSyntaxError(path, str(e))
    return schema
