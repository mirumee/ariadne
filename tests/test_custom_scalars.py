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

    type Query {
        testSerialize: DateReadOnly!
        testInput(value: DateInput!): Boolean!
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


datereadonly = ScalarType("DateReadOnly")


@datereadonly.serializer
def serialize_date(date):
    return date.strftime("%Y-%m-%d")


dateinput = ScalarType("DateInput")


@dateinput.value_parser
def parse_date_str(formatted_date):
    parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
    return parsed_datetime.date()


@dateinput.literal_parser
def parse_date_literal(ast):
    if not isinstance(ast, StringValueNode):
        raise ValueError()

    formatted_date = ast.value
    parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
    return parsed_datetime.date()


schema = make_executable_schema(type_defs, [query, datereadonly, dateinput])


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
    result = graphql_sync(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_attempt_deserialize_str_literal_without_valid_date_raises_error():
    test_input = "invalid string"
    result = graphql_sync(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        'Expected type DateInput!, found "invalid string"; '
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_attempt_deserialize_wrong_type_literal_raises_error():
    test_input = 123
    result = graphql_sync(schema, "{ testInput(value: %s) }" % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Expected type DateInput!, found 123."
    ]


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
        "Expected type DateInput; "
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_attempt_deserialize_wrong_type_variable_raises_error():
    variables = {"value": 123}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Variable '$value' got invalid value 123; Expected type DateInput; "
        "strptime() argument 1 must be str, not int"
    ]


def test_scalar_serializer_can_be_set_on_initialization():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateReadOnly", serializer=serialize_date)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateReadOnly")
    assert schema_scalar.serialize is serialize_date


def test_scalar_serializer_can_be_set_with_setter():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateReadOnly")
    scalar.set_serializer(serialize_date)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateReadOnly")
    assert schema_scalar.serialize is serialize_date


def test_scalar_value_parser_can_be_set_on_initialization():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateReadOnly", value_parser=parse_date_str)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateReadOnly")
    assert schema_scalar.parse_value is parse_date_str


def test_scalar_value_parser_can_be_set_with_setter():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateReadOnly")
    scalar.set_value_parser(parse_date_str)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateReadOnly")
    assert schema_scalar.parse_value is parse_date_str


def test_scalar_literal_parser_can_be_set_on_initialization():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput", literal_parser=parse_date_literal)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_literal is parse_date_literal


def test_scalar_value_parser_can_be_set_with_setter():
    schema = build_schema(type_defs)
    scalar = ScalarType("DateInput")
    scalar.set_literal_parser(parse_date_literal)
    scalar.bind_to_schema(schema)

    schema_scalar = schema.type_map.get("DateInput")
    assert schema_scalar.parse_literal is parse_date_literal
