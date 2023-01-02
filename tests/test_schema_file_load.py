import pathlib

import pytest

from ariadne import exceptions, load_schema_from_path

FIRST_SCHEMA = """
    type Query {
        test: Custom
    }

    type Custom {
        node: String
        default: String
    }
"""


@pytest.fixture(scope="session")
def single_file_schema(tmpdir_factory):
    f = tmpdir_factory.mktemp("schema").join("schema.graphql")
    f.write(FIRST_SCHEMA)
    return f


def test_load_schema_from_single_file(single_file_schema):
    assert load_schema_from_path(str(single_file_schema)) == FIRST_SCHEMA
    assert load_schema_from_path(pathlib.Path(single_file_schema)) == FIRST_SCHEMA


INCORRECT_SCHEMA = """
    type Query {
        test: Custom

    type Custom {
        node: String
        default: String
    }
"""


@pytest.fixture(scope="session")
def incorrect_schema_file(tmpdir_factory):
    f = tmpdir_factory.mktemp("schema").join("schema.graphql")
    f.write(INCORRECT_SCHEMA)
    return f


def test_loading_schema_fails_on_bad_syntax(incorrect_schema_file):
    with pytest.raises(exceptions.GraphQLFileSyntaxError) as e:
        load_schema_from_path(str(incorrect_schema_file))
    assert str(incorrect_schema_file) in str(e.value)


SECOND_SCHEMA = """
    type User {
        name: String
    }
"""


@pytest.fixture
def schema_directory(tmpdir_factory):
    directory = tmpdir_factory.mktemp("schema")
    first_file = directory.join("base.graphql")
    first_file.write_text(FIRST_SCHEMA, encoding="utf-8")
    second_file = directory.join("user.graphql")
    second_file.write_text(SECOND_SCHEMA, encoding="utf-8")
    return directory


def test_loading_schema_from_directory(schema_directory):
    assert load_schema_from_path(str(schema_directory)) == "\n".join(
        [FIRST_SCHEMA, SECOND_SCHEMA]
    )
    assert load_schema_from_path(pathlib.Path(schema_directory)) == "\n".join(
        [FIRST_SCHEMA, SECOND_SCHEMA]
    )


@pytest.fixture
def schema_nested_directories(tmp_path_factory):
    directory = tmp_path_factory.mktemp("schema")
    nested_dir = pathlib.Path(directory.resolve(), "nested")
    nested_dir.mkdir()
    first_file = pathlib.Path(directory.resolve(), "base.graphql")
    first_file.write_text(FIRST_SCHEMA, encoding="utf-8")
    second_file = pathlib.Path(nested_dir.resolve(), "user.graphql")
    second_file.write_text(SECOND_SCHEMA, encoding="utf-8")
    return directory


def test_loading_schema_from_nested_directories(schema_nested_directories):
    assert load_schema_from_path(str(schema_nested_directories)) == "\n".join(
        [FIRST_SCHEMA, SECOND_SCHEMA]
    )
