from dataclasses import dataclass

import pytest
from graphql import graphql_sync

from ariadne import InputType, make_executable_schema


@pytest.fixture
def schema():
    return make_executable_schema(
        """
            type Query {
                repr(input: ExampleInput!): Boolean!
            }

            input ExampleInput {
                id: ID
                message: String
                yearOfBirth: Int
            }
        """
    )


def set_repr_resolver(schema, repr_resolver):
    def resolve_repr(*_, input):
        repr_resolver(input)
        return True

    schema.type_map["Query"].fields["repr"].resolve = resolve_repr


TEST_QUERY = """
query InputTest($input: ExampleInput!) {
    repr(input: $input)
}
"""


def test_attempt_bind_input_type_to_undefined_type_raises_error(schema):
    input_type = InputType("Test")
    with pytest.raises(ValueError):
        input_type.bind_to_schema(schema)


def test_attempt_bind_input_type_to_invalid_type_raises_error(schema):
    input_type = InputType("Query")
    with pytest.raises(ValueError):
        input_type.bind_to_schema(schema)


def test_attempt_bind_input_type_out_name_to_undefined_field_raises_error(schema):
    input_type = InputType("Query", out_names={"undefined": "Ok"})
    with pytest.raises(ValueError):
        input_type.bind_to_schema(schema)


def test_bind_input_type_out_type_sets_custom_python_type_for_input(schema):
    @dataclass
    class InputDataclass:
        id: str
        message: str
        yearOfBirth: int  # noqa: N815

    input_type = InputType(
        "ExampleInput",
        out_type=lambda data: InputDataclass(**data),
    )
    input_type.bind_to_schema(schema)

    def assert_input_type(input):
        assert isinstance(input, InputDataclass)
        assert input.id == "123"
        assert input.message == "Lorem ipsum"
        assert input.yearOfBirth == 2022

    set_repr_resolver(schema, assert_input_type)

    result = graphql_sync(
        schema,
        TEST_QUERY,
        variable_values={
            "input": {
                "id": "123",
                "message": "Lorem ipsum",
                "yearOfBirth": 2022,
            }
        },
    )

    assert not result.errors


def test_bind_input_type_out_names_sets_custom_python_dict_keys_for_input(schema):
    input_type = InputType(
        "ExampleInput",
        out_names={"yearOfBirth": "year_of_birth"},
    )
    input_type.bind_to_schema(schema)

    def assert_input_type(input):
        assert input == {
            "id": "123",
            "message": "Lorem ipsum",
            "year_of_birth": 2022,
        }

    set_repr_resolver(schema, assert_input_type)

    result = graphql_sync(
        schema,
        TEST_QUERY,
        variable_values={
            "input": {
                "id": "123",
                "message": "Lorem ipsum",
                "yearOfBirth": 2022,
            }
        },
    )

    assert not result.errors


def test_bind_input_type_out_type_and_names_sets_custom_python_type_for_input(schema):
    @dataclass
    class InputDataclass:
        id: str
        message: str
        year_of_birth: int

    input_type = InputType(
        "ExampleInput",
        out_type=lambda data: InputDataclass(**data),
        out_names={"yearOfBirth": "year_of_birth"},
    )
    input_type.bind_to_schema(schema)

    def assert_input_type(input):
        assert isinstance(input, InputDataclass)
        assert input.id == "123"
        assert input.message == "Lorem ipsum"
        assert input.year_of_birth == 2022

    set_repr_resolver(schema, assert_input_type)

    result = graphql_sync(
        schema,
        TEST_QUERY,
        variable_values={
            "input": {
                "id": "123",
                "message": "Lorem ipsum",
                "yearOfBirth": 2022,
            }
        },
    )

    assert not result.errors
