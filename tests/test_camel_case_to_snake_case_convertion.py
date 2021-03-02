import pytest

from ariadne import convert_camel_case_to_snake


def test_lower_case_name_is_not_changed():
    test_str = "test"
    assert convert_camel_case_to_snake(test_str) == test_str


def test_two_words_snake_case_name_is_not_changed():
    test_str = "test_name"
    assert convert_camel_case_to_snake(test_str) == test_str


def test_three_words_snake_case_name_is_not_changed():
    test_str = "test_complex_name"
    assert convert_camel_case_to_snake(test_str) == test_str


def test_pascal_case_name_is_lowercased():
    assert convert_camel_case_to_snake("Test") == "test"


def test_two_words_pascal_case_name_is_converted():
    assert convert_camel_case_to_snake("TestName") == "test_name"


def test_two_words_camel_case_name_is_converted():
    assert convert_camel_case_to_snake("testName") == "test_name"


def test_three_words_pascal_case_name_is_converted():
    assert convert_camel_case_to_snake("TestComplexName") == "test_complex_name"


def test_three_words_camel_case_name_is_converted():
    assert convert_camel_case_to_snake("testComplexName") == "test_complex_name"


def test_no_underscore_added_if_previous_character_is_an_underscore():
    assert convert_camel_case_to_snake("test__complexName") == "test__complex_name"


def test_no_underscore_added_if_previous_character_is_uppercase():
    assert convert_camel_case_to_snake("testWithUPPERPart") == "test_with_upper_part"


@pytest.mark.parametrize(
    ("test_str", "result"),
    [
        ("testWith365InIt", "test_with_365_in_it"),
        ("365testWithInIt", "365_test_with_in_it"),
        ("testWithInIt365", "test_with_in_it_365"),
    ],
)
def test_digits_are_treated_as_word(test_str, result):
    assert convert_camel_case_to_snake(test_str) == result
