from ariadne import make_executable_schema

query_definition = '''
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
'''

enum_definition = '''
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
'''


def test_enums_include_descriptions():
    schema = make_executable_schema(enum_definition)

    description = schema.get_type("Language").description
    assert description == "The set of languages supported by `translate`."


def test_enum_values_include_descriptions():
    schema = make_executable_schema(enum_definition)

    for value in schema.get_type("Language").values.values():
        assert isinstance(value.description, str)


def test_object_types_include_descriptions():
    schema = make_executable_schema([query_definition, enum_definition])

    description = schema.get_type("Query").description
    assert description == "A simple GraphQL schema which is well described."


def test_object_fields_include_descriptions():
    schema = make_executable_schema([query_definition, enum_definition])

    description = schema.get_type("Query").fields.get("translate").description
    assert (
        description
        == "Translates a string from a given language into a different language."
    )


def test_object_field_arguments_include_descriptions():
    schema = make_executable_schema([query_definition, enum_definition])

    translate_field = schema.get_type("Query").fields.get("translate")

    for argument in translate_field.args.values():
        assert isinstance(argument.description, str)
