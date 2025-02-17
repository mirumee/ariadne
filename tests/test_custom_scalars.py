from datetime import date, datetime

import pytest
from graphql import build_schema, graphql_sync
from graphql.language.ast import StringValueNode

from ariadne import QueryType, ScalarType, make_executable_schema

TEST_DATE = date(2006, 9, 13)
TEST_DATE_SERIALIZED = TEST_DATE.strftime("%Y-%m-%d")

type_defs = """
    scalar DateReadOnly
    scalar DateInput
    scalar ScalarWithDefaultParser

    type Query {
        testSerialize: DateReadOnly!
        testInput(value: DateInput!): Boolean!
        testInputValueType(value: ScalarWithDefaultParser!): String!
    }
"""

query = QueryType()


@query.field("testSerialize")
def resolve_test_serialize(*_):
    return TEST_DATE


@query.field("testInput")
def resolve_test_input(*_, value):
    assert value == TEST_DATE
    return True


@query.field("testInputValueType")
def resolve_test_input_type(*_, value):
    return value


datereadonly = ScalarType("DateReadOnly")


@datereadonly.serializer
def serialize_date(date):
    return date.strftime("%Y-%m-%d")


dateinput = ScalarType("DateInput")


@dateinput.value_parser
def parse_date_value(formatted_date):
    parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
    return parsed_datetime.date()


@dateinput.literal_parser
def parse_date_literal(ast, variable_values=None):
    if not isinstance(ast, StringValueNode):
        raise ValueError()

    formatted_date = ast.value
    parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
    return parsed_datetime.date()


scalar_with_default_parser = ScalarType("ScalarWithDefaultParser")


@scalar_with_default_parser.value_parser
def parse_value_from_default_literal_parser(value):
    return type(value).__name__


schema = make_executable_schema(
    type_defs, [query, datereadonly, dateinput, scalar_with_default_parser]
)


def test_attempt_bind_scalar_to_undefined_type_raises_error():
    schema = build_schema(type_defs)
    scalar = ScalarType("Test")
    with pytest.raises(ValueError):
        scalar.bind_to_schema(schema)


def test_attempt_bind_scalar_to_invalid_schema_type_raises_error():
    schema = build_schema(type_defs)
    scalar = ScalarType("Query")
    with pytest.raises(ValueError):
        scalar.bind_to_schema(schema)


def test_python_date_is_serialized_by_scalar():
    result = graphql_sync(schema, "{ testSerialize }")
    assert result.errors is None
    assert result.data == {"testSerialize": TEST_DATE_SERIALIZED}


def test_literal_with_valid_date_str_is_deserialized_to_python_date():
    test_input = TEST_DATE_SERIALIZED
    result = graphql_sync(schema, f'{{ testInput(value: "{test_input}") }}')
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_attempt_deserialize_str_literal_without_valid_date_raises_error():
    test_input = "invalid string"
    result = graphql_sync(schema, f'{{ testInput(value: "{test_input}") }}')
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Expected value of type 'DateInput!', found \"invalid string\"; "
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_attempt_deserialize_wrong_type_literal_raises_error():
    test_input = 123
    result = graphql_sync(schema, f"{{ testInput(value: {test_input}) }}")
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Expected value of type 'DateInput!', found 123; "
    ]


def test_default_literal_parser_is_used_to_extract_value_str_from_ast_node():
    dateinput = ScalarType("DateInput")
    dateinput.set_value_parser(parse_date_value)
    schema = make_executable_schema(type_defs, query, dateinput)

    result = graphql_sync(
        schema, f"""{{ testInput(value: "{TEST_DATE_SERIALIZED}") }}"""
    )
    assert result.errors is None
    assert result.data == {"testInput": True}


parametrized_query = """
    query parseValueTest($value: DateInput!) {
        testInput(value: $value)
    }
"""


def test_variable_with_valid_date_string_is_deserialized_to_python_date():
    variables = {"value": TEST_DATE_SERIALIZED}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_attempt_deserialize_str_variable_without_valid_date_raises_error():
    variables = {"value": "invalid string"}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Variable '$value' got invalid value 'invalid string'; "
        "Expected type 'DateInput'. "
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_attempt_deserialize_wrong_type_variable_raises_error():
    variables = {"value": 123}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Variable '$value' got invalid value 123; Expected type 'DateInput'. "
        "strptime() argument 1 must be str, not int"
    ]


def test_scalar_serializer_can_be_set_on_initialization():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput", serializer=serialize_date)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.serialize is serialize_date


def test_scalar_serializer_can_be_set_with_setter():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput")
    scalar.set_serializer(serialize_date)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.serialize is serialize_date


def test_scalar_value_parser_can_be_set_on_initialization():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput", value_parser=parse_date_value)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_value is parse_date_value


def test_scalar_value_parser_can_be_set_with_setter():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput")
    scalar.set_value_parser(parse_date_value)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_value is parse_date_value


def test_scalar_literal_parser_can_be_set_on_initialization():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput", literal_parser=parse_date_literal)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_literal is parse_date_literal


def test_scalar_literal_parser_can_be_set_with_setter():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput")
    scalar.set_literal_parser(parse_date_literal)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_literal is parse_date_literal


def test_setting_scalar_value_parser_sets_default_literal_parsers_if_none_is_set():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput")
    scalar.set_value_parser(parse_date_value)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_value is parse_date_value
    assert schema_scalar.parse_literal


def test_literal_string_is_deserialized_by_default_parser():
    result = graphql_sync(schema, '{ testInputValueType(value: "test") }')
    assert result.errors is None
    assert result.data == {"testInputValueType": "str"}


def test_literal_int_is_deserialized_by_default_parser():
    result = graphql_sync(schema, "{ testInputValueType(value: 123) }")
    assert result.errors is None
    assert result.data == {"testInputValueType": "int"}


def test_literal_float_is_deserialized_by_default_parser():
    result = graphql_sync(schema, "{ testInputValueType(value: 1.5) }")
    assert result.errors is None
    assert result.data == {"testInputValueType": "float"}


def test_literal_bool_true_is_deserialized_by_default_parser():
    result = graphql_sync(schema, "{ testInputValueType(value: true) }")
    assert result.errors is None
    assert result.data == {"testInputValueType": "bool"}


def test_literal_bool_false_is_deserialized_by_default_parser():
    result = graphql_sync(schema, "{ testInputValueType(value: false) }")
    assert result.errors is None
    assert result.data == {"testInputValueType": "bool"}


def test_literal_object_is_deserialized_by_default_parser():
    result = graphql_sync(schema, "{ testInputValueType(value: {}) }")
    assert result.errors is None
    assert result.data == {"testInputValueType": "dict"}


def test_literal_list_is_deserialized_by_default_parser():
    result = graphql_sync(schema, "{ testInputValueType(value: []) }")
    assert result.errors is None
    assert result.data == {"testInputValueType": "list"}
