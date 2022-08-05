import pytest

from ariadne import (
    QueryType,
    make_executable_schema,
    graphql_sync,
    convert_kwargs_to_snake_case,
)


def test_decorator_converts_kwargs_to_camel_case():
    @convert_kwargs_to_snake_case
    def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    wrapped_func(
        firstParameter=True,
        secondParameter="value",
        nestedParameter={"firstSubEntry": 1, "secondSubEntry": 2},
    )


def test_decorator_converts_kwargs_to_camel_case_for_mapping(fake_mapping):
    @convert_kwargs_to_snake_case
    def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    wrapped_func(
        firstParameter=True,
        secondParameter="value",
        nestedParameter=fake_mapping(firstSubEntry=1, secondSubEntry=2),
    )


def test_decorator_leaves_snake_case_kwargs_unchanged():
    @convert_kwargs_to_snake_case
    def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    wrapped_func(
        first_parameter=True,
        second_parameter="value",
        nested_parameter={"first_sub_entry": 1, "second_sub_entry": 2},
    )


def test_decorator_converts_objects_in_lists_to_camel_case():
    @convert_kwargs_to_snake_case
    def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "list_of_items": [
                {"first_property": 1, "second_property": 2},
            ],
        }

    wrapped_func(
        firstParameter=True,
        listOfItems=[{"firstProperty": 1, "secondProperty": 2}],
    )


def test_decorator_converts_mappings_in_lists_to_camel_case(fake_mapping):
    @convert_kwargs_to_snake_case
    def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "list_of_items": [
                {"first_property": 1, "second_property": 2},
            ],
        }

    wrapped_func(
        firstParameter=True,
        listOfItems=[fake_mapping(firstProperty=1, secondProperty=2)],
    )


def test_decorator_leaves_primitives_in_lists_unchanged():
    @convert_kwargs_to_snake_case
    def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "list_of_items": ["firstItem", "secondItem"],
        }

    wrapped_func(
        firstParameter=True,
        listOfItems=["firstItem", "secondItem"],
    )


@pytest.mark.asyncio
async def test_decorator_converts_kwargs_to_camel_case_for_async_resolver():
    @convert_kwargs_to_snake_case
    async def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    await wrapped_func(
        firstParameter=True,
        secondParameter="value",
        nestedParameter={"firstSubEntry": 1, "secondSubEntry": 2},
    )


@pytest.mark.asyncio
async def test_decorator_leaves_snake_case_kwargs_unchanged_for_async_resolver():
    @convert_kwargs_to_snake_case
    async def wrapped_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    await wrapped_func(
        first_parameter=True,
        second_parameter="value",
        nested_parameter={"first_sub_entry": 1, "second_sub_entry": 2},
    )


@pytest.mark.parametrize(
    "convert_args_to_snake_case",
    [False, None, True, "any truthy value"],
)
def test_global_option_for_camel_to_snake_case(convert_args_to_snake_case):
    type_defs = """
        input I {
            F00: Int
            complexField_Int32: Int
        }
        type Query {
            test (arg: Int, x_arg: Int, argTypeI: I): String
        }
    """
    query_type = QueryType()
    kwargs = None

    @query_type.field("test")
    def resolve(*_, **_kwargs):
        nonlocal kwargs
        kwargs = _kwargs
        return ""

    schema = make_executable_schema(
        type_defs, query_type, convert_args_to_snake_case=convert_args_to_snake_case
    )
    success, result = graphql_sync(
        schema,
        {
            "query": "{test (arg: 0, x_arg: 0, argTypeI: {F00: 0, complexField_Int32: 0})}"
        },
    )
    assert success and result["data"] == {"test": ""}
    expect = (
        {
            "arg": 0,
            "x_arg": 0,
            "arg_type_i": {"f_00": 0, "complex_field__int_32": 0},
        }
        if convert_args_to_snake_case
        else {
            "arg": 0,
            "x_arg": 0,
            "argTypeI": {"F00": 0, "complexField_Int32": 0},
        }
    )
    assert kwargs == expect
