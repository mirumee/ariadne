from datetime import date, datetime

import pytest
from graphql import build_schema, graphql_sync
from graphql.language.ast import StringValueNode

from ariadne import ResolverMap, Scalar, make_executable_schema

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

query = ResolverMap("Query")


@query.field("testSerialize")
def resolve_test_serialize(*_):
    return TEST_DATE


@query.field("testInput")
def resolve_test_input(*_, value):
    assert value == TEST_DATE
    return True


datereadonly = Scalar("DateReadOnly")


@datereadonly.serializer
def serialize(date):
    return date.strftime("%Y-%m-%d")


dateinput = Scalar("DateInput")


@dateinput.value_parser
def parse_value(formatted_date):
    parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
    return parsed_datetime.date()


@dateinput.literal_parser
def parse_literal(ast):
    if not isinstance(ast, StringValueNode):
        raise ValueError()

    formatted_date = ast.value
    parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
    return parsed_datetime.date()


schema = make_executable_schema(type_defs, [query, datereadonly, dateinput])


def test_if_scalar_is_not_defined_in_schema_value_error_is_raised():
    schema = build_schema(type_defs)
    scalar = Scalar("Test")
    with pytest.raises(ValueError):
        scalar.bind_to_schema(schema)


def test_if_scalar_is_defined_in_schema_but_is_incorrect_value_error_is_raised():
    schema = build_schema(type_defs)
    scalar = Scalar("Query")
    with pytest.raises(ValueError):
        scalar.bind_to_schema(schema)


def test_serialize_date_obj_to_date_str():
    result = graphql_sync(schema, "{ testSerialize }")
    assert result.errors is None
    assert result.data == {"testSerialize": TEST_DATE_SERIALIZED}


def test_parse_literal_valid_str_ast_to_date_instance():
    test_input = TEST_DATE_SERIALIZED
    result = graphql_sync(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_parse_literal_invalid_str_ast_to_date_instance():
    test_input = "invalid string"
    result = graphql_sync(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        'Expected type DateInput!, found "invalid string"; '
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_parse_literal_invalid_int_ast_errors():
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


def test_parse_value_valid_date_str_returns_date_instance():
    variables = {"value": TEST_DATE_SERIALIZED}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_parse_value_invalid_str_errors():
    variables = {"value": "invalid string"}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Variable '$value' got invalid value 'invalid string'; "
        "Expected type DateInput; "
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_parse_value_invalid_value_type_int_errors():
    variables = {"value": 123}
    result = graphql_sync(schema, parametrized_query, variable_values=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Variable '$value' got invalid value 123; Expected type DateInput; "
        "strptime() argument 1 must be str, not int"
    ]
