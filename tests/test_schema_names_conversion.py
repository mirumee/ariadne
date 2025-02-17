from graphql import graphql_sync

from ariadne import QueryType, gql, make_executable_schema


def test_field_names_without_resolvers_are_converted():
    type_defs = gql(
        """
        type Query {
            field: String
            convertedField: String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=True)
    result = graphql_sync(
        schema,
        "{ field convertedField }",
        root_value={
            "field": "works",
            "converted_field": "okay",
        },
    )

    assert result.data == {"field": "works", "convertedField": "okay"}


def test_field_names_with_resolvers_are_not_converted():
    type_defs = gql(
        """
        type Query {
            field: String
            convertedField: String
        }
        """
    )

    query_type = QueryType()
    query_type.set_field("convertedField", lambda *_: "lambda")

    schema = make_executable_schema(type_defs, query_type, convert_names_case=True)
    result = graphql_sync(
        schema,
        "{ field convertedField }",
        root_value={
            "field": "works",
            "converted_field": "okay",
        },
    )

    assert result.data == {"field": "works", "convertedField": "lambda"}


def test_field_names_without_need_for_conversion_are_skipped():
    type_defs = gql(
        """
        type Query {
            field: String
            convertedField: String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=True)
    assert schema.type_map["Query"].fields["field"].resolve is None
    assert schema.type_map["Query"].fields["convertedField"].resolve is not None


def test_fields_arguments_are_converted():
    type_defs = gql(
        """
        type Query {
            field(arg: String, otherArg: Int): String
            convertedField(arg: String, otherArg: Int): String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=True)
    query_type = schema.type_map["Query"]
    field = query_type.fields["field"]
    converted_field = query_type.fields["convertedField"]

    # Args that don't need conversion are skipped
    assert field.args["arg"].out_name is None
    assert converted_field.args["arg"].out_name is None

    # Input field names that need conversion have out_name set
    assert field.args["otherArg"].out_name == "other_arg"
    assert converted_field.args["otherArg"].out_name == "other_arg"


def test_inputs_field_names_are_converted():
    type_defs = gql(
        """
        type Query {
            _skip: String
        }

        input Test {
            field: String
            convertedField: String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=True)
    input_type = schema.type_map["Test"]

    # Input field names that don't need conversion are skipped
    assert input_type.fields["field"].out_name is None

    # Input field names that need conversion have out_name set
    assert input_type.fields["convertedField"].out_name == "converted_field"


def test_fields_converted_argument_names_are_used():
    type_defs = gql(
        """
        type Query {
            test(arg: String, otherArg: String): String
        }
        """
    )

    query_type = QueryType()

    @query_type.field("test")
    def resolve_test(*_, arg=None, other_arg=None):
        return arg + other_arg

    schema = make_executable_schema(type_defs, query_type, convert_names_case=True)

    result = graphql_sync(schema, '{ test(arg: "Lorem", otherArg: "Ipsum") }')
    assert result.data == {"test": "LoremIpsum"}


def test_inputs_converted_fields_names_are_used():
    type_defs = gql(
        """
        type Query {
            test(input: TestInput): String
        }

        input TestInput {
            field: String
            convertedField: String
        }
        """
    )

    query_type = QueryType()

    @query_type.field("test")
    def resolve_test(*_, input=None):
        return input["field"] + input["converted_field"]

    schema = make_executable_schema(type_defs, query_type, convert_names_case=True)

    result = graphql_sync(
        schema, '{ test(input: { field: "Lorem", convertedField: "Ipsum"}) }'
    )
    assert result.data == {"test": "LoremIpsum"}


def custom_converter(graphql_name, schema, path):
    assert schema
    assert path
    assert path[-1] == graphql_name
    return f"custom_{graphql_name}"


def test_field_names_are_converted_using_custom_strategy():
    type_defs = gql(
        """
        type Query {
            field: String
            convertedField: String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=custom_converter)
    result = graphql_sync(
        schema,
        "{ field convertedField }",
        root_value={
            "field": "works",
            "custom_convertedField": "okay",
        },
    )

    assert result.data == {"field": "works", "convertedField": "okay"}


def test_field_arguments_are_converted_using_custom_strategy():
    type_defs = gql(
        """
        type Query {
            field(arg: String, otherArg: Int): String
            convertedField(arg: String, otherArg: Int): String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=custom_converter)
    query_type = schema.type_map["Query"]
    field = query_type.fields["field"]
    converted_field = query_type.fields["convertedField"]

    # Args that don't need conversion are skipped
    assert field.args["arg"].out_name is None
    assert converted_field.args["arg"].out_name is None

    # Input field names that need conversion have out_name set
    assert field.args["otherArg"].out_name == "custom_otherArg"
    assert converted_field.args["otherArg"].out_name == "custom_otherArg"


def test_inputs_field_names_are_converted_using_custom_strategy():
    type_defs = gql(
        """
        type Query {
            _skip: String
        }

        input Test {
            field: String
            convertedField: String
        }
        """
    )

    schema = make_executable_schema(type_defs, convert_names_case=custom_converter)
    input_type = schema.type_map["Test"]

    # Input field names that don't need conversion are skipped
    assert input_type.fields["field"].out_name is None

    # Input field names that need conversion have out_name set
    assert input_type.fields["convertedField"].out_name == "custom_convertedField"
