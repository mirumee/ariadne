import pytest

from ariadne import convert_kwargs_to_snake_case


def test_decorator_converts_kwargs_to_camel_case():
    @convert_kwargs_to_snake_case
    def my_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    my_func(
        firstParameter=True,
        secondParameter="value",
        nestedParameter={"firstSubEntry": 1, "secondSubEntry": 2},
    )


def test_decorator_leaves_snake_case_kwargs_unchanged():
    @convert_kwargs_to_snake_case
    def my_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    my_func(
        first_parameter=True,
        second_parameter="value",
        nested_parameter={"first_sub_entry": 1, "second_sub_entry": 2},
    )


def test_decorator_converts_objects_in_lists_to_camel_case():
    @convert_kwargs_to_snake_case
    def my_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "list_of_items": [
                {"first_property": 1, "second_property": 2},
            ],
        }

    my_func(
        firstParameter=True,
        listOfItems=[{"firstProperty": 1, "secondProperty": 2}],
    )


def test_decorator_leaves_primitives_in_lists_unchanged():
    @convert_kwargs_to_snake_case
    def my_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "list_of_items": ["firstItem", "secondItem"],
        }

    my_func(
        firstParameter=True,
        listOfItems=["firstItem", "secondItem"],
    )


@pytest.mark.asyncio
async def test_decorator_converts_kwargs_to_camel_case_for_async_resolver():
    @convert_kwargs_to_snake_case
    async def my_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    await my_func(
        firstParameter=True,
        secondParameter="value",
        nestedParameter={"firstSubEntry": 1, "secondSubEntry": 2},
    )


@pytest.mark.asyncio
async def test_decorator_leaves_snake_case_kwargs_unchanged_for_async_resolver():
    @convert_kwargs_to_snake_case
    async def my_func(*_, **kwargs):
        assert kwargs == {
            "first_parameter": True,
            "second_parameter": "value",
            "nested_parameter": {"first_sub_entry": 1, "second_sub_entry": 2},
        }

    await my_func(
        first_parameter=True,
        second_parameter="value",
        nested_parameter={"first_sub_entry": 1, "second_sub_entry": 2},
    )
