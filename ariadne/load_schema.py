import os
from typing import Generator, Union

from graphql import parse
from graphql.error import GraphQLSyntaxError

from .exceptions import GraphQLFileSyntaxError


def load_schema_from_path(path: Union[str, bytes, os.PathLike]) -> str:
    if os.path.isdir(path):
        schema_list = [read_graphql_file(f) for f in sorted(walk_graphql_files(path))]
        return "\n".join(schema_list)
    return read_graphql_file(os.path.abspath(path))


def walk_graphql_files(
    path: Union[str, bytes, os.PathLike]
) -> Generator[str, None, None]:
    extensions = (".graphql", ".graphqls", ".gql")
    for dirpath, _, files in os.walk(str(path)):
        for name in files:
            if name.lower().endswith(extensions):
                yield os.path.join(dirpath, name)


def read_graphql_file(path: Union[str, bytes, os.PathLike]) -> str:
    with open(path, "r", encoding="utf-8") as graphql_file:
        schema = graphql_file.read()
    try:
        parse(schema)
    except GraphQLSyntaxError as e:
        raise GraphQLFileSyntaxError(path, str(e)) from e
    return schema
