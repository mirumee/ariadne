import pytest

from ariadne.explorer.template import render_template


def test_plain_string_is_rendered():
    assert render_template("plain text") == "plain text"


def test_string_and_var_is_rendered():
    assert render_template("Hi {{ name }}!", {"name": "Alice"}) == "Hi Alice!"


def test_var_is_rendered_escaped():
    assert (
        render_template("Hi {{ name }}!", {"name": '<Al"ice>'})
        == "Hi &lt;Al&quot;ice&gt;!"
    )


def test_missing_var_is_rendered_as_blank_str():
    assert render_template("Hi {{ name }}!") == "Hi !"


def test_var_is_cast_to_str():
    assert (
        render_template("Hi {{ name }}!", {"name": {"a": 42}})
        == "Hi {&#x27;a&#x27;: 42}!"
    )


def test_string_is_rendered_inside_if_block():
    assert (
        render_template("Hi {% if greet %}user{% endif %}!", {"greet": True})
        == "Hi user!"
    )


def test_var_is_rendered_inside_if_block():
    assert (
        render_template(
            "Hi {% if greet %}{{ name }}{% endif %}!", {"greet": True, "name": "Alice"}
        )
        == "Hi Alice!"
    )


def test_var_is_not_rendered_inside_if_block_for_false_condition():
    assert (
        render_template(
            "Hi {% if greet %}{{ name }}{% endif %}!", {"greet": False, "name": "Alice"}
        )
        == "Hi !"
    )


def test_else_clause_is_rendered_by_if_block():
    assert (
        render_template("Hi {% if name %}{{ name }}{% else %}guest{% endif %}!")
        == "Hi guest!"
    )


def test_var_is_rendered_inside_ifnot_block():
    assert (
        render_template(
            "Hi {% ifnot greet %}{{ name }}{% endif %}!",
            {"greet": False, "name": "Alice"},
        )
        == "Hi Alice!"
    )


def test_var_is_not_rendered_inside_ifnot_block():
    assert (
        render_template(
            "Hi {% ifnot greet %}{{ name }}{% endif %}!",
            {"greet": True, "name": "Alice"},
        )
        == "Hi !"
    )


def test_blocks_support_nesting():
    tpl = "Hi {% if a %}{% ifnot b %}a{% else %}b{% endif %}{% else %}c{% endif %}!"
    assert render_template(tpl, {"a": "a", "b": "b", "c": "c"}) == "Hi b!"
    assert render_template(tpl, {"a": "a", "b": "", "c": "c"}) == "Hi a!"
    assert render_template(tpl, {"a": "", "b": "b", "c": "c"}) == "Hi c!"


def test_multiple_else_in_if_block_raises_error():
    with pytest.raises(ValueError):
        render_template(
            "Hi {% if greet %}a{% else %}b{% else %}c{% endif %}!",
            {"greet": True},
        )


def test_unescaped_var_is_rendered_using_raw_block():
    assert (
        render_template("Hi {% raw name %}!", {"name": "<b>Raw</b>"})
        == "Hi <b>Raw</b>!"
    )
