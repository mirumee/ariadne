from datetime import date, datetime

import pytest
from graphql import GraphQLError, StringValueNode, graphql_sync

from ..executable_schema import make_executable_schema
from ..object_type import ObjectType
from ..scalar_type import ScalarType


def test_scalar_type_raises_error_when_defined_without_schema(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class DateScalar(ScalarType):
            pass

    snapshot.assert_match(err)


def test_scalar_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class DateScalar(ScalarType):
            __schema__ = True

    snapshot.assert_match(err)


def test_scalar_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class DateScalar(ScalarType):
            __schema__ = "scalor Date"

    snapshot.assert_match(err)


def test_scalar_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class DateScalar(ScalarType):
            __schema__ = "type DateTime"

    snapshot.assert_match(err)


def test_scalar_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class DateScalar(ScalarType):
            __schema__ = """
            scalar Date

            scalar DateTime
            """

    snapshot.assert_match(err)


def test_scalar_type_extracts_graphql_name():
    class DateScalar(ScalarType):
        __schema__ = "scalar Date"

    assert DateScalar.graphql_name == "Date"


class DateReadOnlyScalar(ScalarType):
    __schema__ = "scalar DateReadOnly"

    @staticmethod
    def serialize(date):
        return date.strftime("%Y-%m-%d")


class DateInputScalar(ScalarType):
    __schema__ = "scalar DateInput"

    @staticmethod
    def parse_value(formatted_date):
        parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
        return parsed_datetime.date()

    @staticmethod
    def parse_literal(ast, variable_values=None):  # pylint: disable=unused-argument
        if not isinstance(ast, StringValueNode):
            raise ValueError()

        formatted_date = ast.value
        parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
        return parsed_datetime.date()


class DefaultParserScalar(ScalarType):
    __schema__ = "scalar DefaultParser"

    @staticmethod
    def parse_value(value):
        return type(value).__name__


TEST_DATE = date(2006, 9, 13)
TEST_DATE_SERIALIZED = TEST_DATE.strftime("%Y-%m-%d")


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        testSerialize: DateReadOnly!
        testInput(value: DateInput!): Boolean!
        testInputValueType(value: DefaultParser!): String!
    }
    """
    __requires__ = [
        DateReadOnlyScalar,
        DateInputScalar,
        DefaultParserScalar,
    ]
    __resolvers__ = {
        "testSerialize": "test_serialize",
        "testInput": "test_input",
        "testInputValueType": "test_input_value_type",
    }

    @staticmethod
    def test_serialize(*_):
        return TEST_DATE

    @staticmethod
    def test_input(*_, value):
        assert value == TEST_DATE
        return True

    @staticmethod
    def test_input_value_type(*_, value):
        return value


schema = make_executable_schema(QueryType)


def test_attempt_deserialize_str_literal_without_valid_date_raises_error():
    test_input = "invalid string"
    result = graphql_sync(schema, '{ testInput(value: "%s") }' % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Expected value of type 'DateInput!', found \"invalid string\"; "
        "time data 'invalid string' does not match format '%Y-%m-%d'"
    ]


def test_attempt_deserialize_wrong_type_literal_raises_error():
    test_input = 123
    result = graphql_sync(schema, "{ testInput(value: %s) }" % test_input)
    assert result.errors is not None
    assert str(result.errors[0]).splitlines()[:1] == [
        "Expected value of type 'DateInput!', found 123; "
    ]


def test_default_literal_parser_is_used_to_extract_value_str_from_ast_node():
    class ValueParserOnlyScalar(ScalarType):
        __schema__ = "scalar DateInput"

        @staticmethod
        def parse_value(formatted_date):
            parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
            return parsed_datetime.date()

    class ValueParserOnlyQueryType(ObjectType):
        __schema__ = """
        type Query {
            parse(value: DateInput!): String!
        }
        """
        __requires__ = [ValueParserOnlyScalar]

        @staticmethod
        def parse(*_, value):
            return value

    schema = make_executable_schema(ValueParserOnlyQueryType)
    result = graphql_sync(schema, """{ parse(value: "%s") }""" % TEST_DATE_SERIALIZED)
    assert result.errors is None
    assert result.data == {"parse": "2006-09-13"}


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
