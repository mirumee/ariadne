from datetime import date, datetime

from graphql import graphql
from graphql.language.ast import StringValue

from ariadne import make_executable_schema

type_defs = """
    scalar Date

    type Query {
        testSerialize: Date!
        testInput(value: Date!): Boolean!
    }
"""


def serialize(date):
    return date.strftime("%Y-%m-%d")


def parse_literal(ast):
    if isinstance(ast, StringValue):
        formatted_date = ast.value
        try:
            parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
            return parsed_datetime.date()
        except ValueError:
            pass
    return None


def parse_value(formatted_date):
    try:
        parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
        return parsed_datetime.date()
    except (TypeError, ValueError):
        return None


def resolve_test_serialize(*_):
    return date.today()


def resolve_test_input(*_, value):
    assert value == date.today()
    return True


resolvers = {
    "Query": {"testSerialize": resolve_test_serialize, "testInput": resolve_test_input},
    "Date": {
        "serializer": serialize,
        "parse_literal": parse_literal,
        "parse_value": parse_value,
    },
}

schema = make_executable_schema(type_defs, resolvers)


def test_serialize_date_obj_to_date_str():
    result = graphql(schema, "{ testSerialize }")
    assert result.errors is None
    assert result.data == {"testSerialize": date.today().strftime("%Y-%m-%d")}


def test_parse_literal_valid_str_ast_to_date_instance():
    test_input = date.today().strftime("%Y-%m-%d")
    result = graphql(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_parse_literal_invalid_str_ast_to_date_instance():
    test_input = "invalid string"
    result = graphql(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines() == [
        'Argument "value" has invalid value "invalid string".',
        'Expected type "Date", found "invalid string".',
    ]


def test_parse_literal_invalid_int_ast_errors():
    test_input = 123
    result = graphql(schema, "{ testInput(value: %s) }" % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines() == [
        'Argument "value" has invalid value 123.',
        'Expected type "Date", found 123.',
    ]


parametrized_query = """
    query parseValueTest($value: Date!) {
        testInput(value: $value)
    }
"""


def test_parse_value_valid_date_str_returns_date_instance():
    variables = {"value": date.today().strftime("%Y-%m-%d")}
    result = graphql(schema, parametrized_query, variables=variables)
    assert result.errors is None
    assert result.data == {"testInput": True}


def test_parse_value_invalid_str_errors():
    variables = {"value": "invalid string"}
    result = graphql(schema, parametrized_query, variables=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines() == [
        'Variable "$value" got invalid value "invalid string".',
        'Expected type "Date", found "invalid string".',
    ]


def test_parse_value_invalid_value_type_int_errors():
    variables = {"value": 123}
    result = graphql(schema, parametrized_query, variables=variables)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines() == [
        'Variable "$value" got invalid value 123.',
        'Expected type "Date", found 123.',
    ]
