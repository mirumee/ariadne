from ariadne import convert_camel_case_to_snake


def test_snake_case_name_is_not_changed():
    test_str = "test"
    assert convert_camel_case_to_snake(test_str) == test_str


def test_two_words_snake_case_name_is_not_changed():
    test_str = "test_name"
    assert convert_camel_case_to_snake(test_str) == test_str


def test_three_words_snake_case_name_is_not_changed():
    test_str = "test_complex_name"
    assert convert_camel_case_to_snake(test_str) == test_str


def test_camel_case_name_is_lowercased():
    assert convert_camel_case_to_snake("Test") == "test"


def test_two_words_camel_case_name_is_converted():
    assert convert_camel_case_to_snake("TestName") == "test_name"


def test_two_words_pascal_case_name_is_converted():
    assert convert_camel_case_to_snake("testName") == "test_name"


def test_three_words_camel_case_name_is_converted():
    assert convert_camel_case_to_snake("TestComplexName") == "test_complex_name"


def test_three_words_pascal_case_name_is_converted():
    assert convert_camel_case_to_snake("testComplexName") == "test_complex_name"
