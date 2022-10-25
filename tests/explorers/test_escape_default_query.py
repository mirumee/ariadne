from ariadne.explorer import escape_default_query


def test_plain_string_is_escaped():
    assert escape_default_query("Hello") == "Hello"


def test_new_line_sign_is_escaped():
    assert escape_default_query("Hello\nWorld") == "Hello\\nWorld"


def test_already_escaped_newline_sign_is_escaped():
    assert escape_default_query("Hello\\nWorld") == "Hello\\nWorld"


def test_incorrectly_escaped_newline_sign_is_escaped():
    assert escape_default_query("Hello\\\\nWorld") == "Hello\\nWorld"


def test_str_sign_is_escaped():
    assert escape_default_query("Hello'World") == "Hello\\'World"


def test_already_escaped_str_sign_is_escaped():
    assert escape_default_query("Hello\\'World") == "Hello\\'World"


def test_incorrectly_escaped_str_sign_is_escaped():
    assert escape_default_query("Hello\\\\'World") == "Hello\\'World"
