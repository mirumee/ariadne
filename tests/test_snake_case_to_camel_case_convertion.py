import pytest

from ariadne import convert_snake_case_to_camel_case


def test_two_words_snake_case_name_is_converted():
    assert convert_snake_case_to_camel_case("test_name") == "testName"


def test_three_words_snake_case_name_is_converted():
    assert convert_snake_case_to_camel_case("test_complex_name") == "testComplexName"


def test_no_underscore_added_if_previous_character_is_an_underscore():
    assert convert_snake_case_to_camel_case("test__complex_name") == "test__complexName"


@pytest.mark.parametrize(
    ("test_str", "result"),
    [
        ("test_with_365_in_it", "testWith365InIt"),
        ("365_test_with_in_it", "365TestWithInIt"),
        ("test_with_in_it_365", "testWithInIt365"),
    ],
)
def test_digits_are_treated_as_word(test_str, result):
    print(convert_snake_case_to_camel_case(test_str))
    assert convert_snake_case_to_camel_case(test_str) == result
