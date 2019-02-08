import pytest

from ariadne import make_executable_schema

type_defs = '''
    """
    A simple GraphQL schema which is well described.
    """
    type Query {
        """
        Translates a string from a given language into a different language.
        """
        translate(
            "The original language that `text` is provided in."
            fromLanguage: Language

            "The translated language to be returned."
            toLanguage: Language

            "The text to be translated."
            text: String
        ): String
    }

    """
    The set of languages supported by `translate`.
    """
    enum Language {
        "English"
        EN

        "French"
        FR

        "Chinese"
        CH
    }

    """
    A poorly documented object type.
    """
    type MyObject {
        myField: String
        transform(a: String): String
    }
'''


@pytest.fixture
def schema():
    return make_executable_schema(type_defs)


def test_enum_has_description(schema):
    description = schema.get_type("Language").description
    assert isinstance(description, str)


def test_enum_value_has_description(schema):
    value = schema.get_type("Language").values.get("EN")
    assert isinstance(value.description, str)


def test_object_type_has_description(schema):
    description = schema.get_type("Query").description
    assert isinstance(description, str)


def test_object_field_has_description(schema):
    description = schema.get_type("Query").fields.get("translate").description
    assert isinstance(description, str)


def test_object_field_argument_has_description(schema):
    translate_field = schema.get_type("Query").fields.get("translate")
    argument = translate_field.args.get("fromLanguage")
    assert isinstance(argument.description, str)


def test_undocumented_object_field_description_is_none(schema):
    description = schema.get_type("MyObject").fields.get("myField").description
    assert description is None


def test_undocumented_object_field_argument_description_is_none(schema):
    my_field = schema.get_type("MyObject").fields.get("transform")
    description = my_field.args.get("a").description
    assert description is None
