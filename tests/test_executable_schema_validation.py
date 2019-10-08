import pytest

from ariadne import make_executable_schema


def test_executable_schema_creation_errors_if_type_defs_is_graphql_query():
    type_defs = """
        query { test }
    """

    with pytest.raises(TypeError):
        make_executable_schema(type_defs)


def test_executable_schema_creation_errors_if_type_defs_is_invalid_schema():
    type_defs = """
        type Mutation {
            test: Boolean!
        }
    """

    with pytest.raises(TypeError):
        make_executable_schema(type_defs)
