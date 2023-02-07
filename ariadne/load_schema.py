import os
from typing import Generator, Union

from graphql import parse
from graphql.error import GraphQLSyntaxError

from .exceptions import GraphQLFileSyntaxError


def load_schema_from_path(path: Union[str, os.PathLike]) -> str:
    """Load schema definition in Schema Definition Language from file or directory.

    If `path` argument points to a file, this file's contents are read, validated
    and returned as `str`. If its a directory, its walked recursively and every
    file with `.graphql`, `.graphqls` or `.gql` extension is read and validated,
    and all files are then concatenated into single `str` that is then returned.

    Returns a `str` with schema definition that was already validated to be valid
    GraphQL SDL. Raises `GraphQLFileSyntaxError` is any of loaded files fails to
    parse.

    # Required arguments

    `path`: a `str` or `PathLike` object pointing to either file or directory
    with files to load.
    """
    if os.path.isdir(path):
        schema_list = [read_graphql_file(f) for f in sorted(walk_graphql_files(path))]
        return "\n".join(schema_list)
    return read_graphql_file(os.path.abspath(path))


def walk_graphql_files(path: Union[str, os.PathLike]) -> Generator[str, None, None]:
    extensions = (".graphql", ".graphqls", ".gql")
    for dirpath, _, files in os.walk(str(path)):
        for name in files:
            if name.lower().endswith(extensions):
                yield os.path.join(dirpath, name)


def read_graphql_file(path: Union[str, os.PathLike]) -> str:
    with open(path, "r", encoding="utf-8") as graphql_file:
        schema = graphql_file.read()
    try:
        parse(schema)
    except GraphQLSyntaxError as e:
        raise GraphQLFileSyntaxError(path, str(e)) from e
    return schema
