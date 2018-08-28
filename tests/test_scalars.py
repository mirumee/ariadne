from datetime import date, datetime

from graphql import graphql
from graphql.language.ast import StringValue

from ariadne import make_executable_schema


def test_serialize_custom_scalar():
    type_defs = """
        scalar Date

        type Query {
            test: Date
        }
    """

    resolvers = {
        "Query": {"test": lambda *_: date.today()},
        "Date": {"serializer": lambda date: date.strftime("%Y-%m-%d")},
    }

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test }")
    assert result.errors is None
    assert result.data == {"test": date.today().strftime("%Y-%m-%d")}


def test_deserialize_custom_scalar():
    type_defs = """
        scalar Date

        type Query {
            test(value: Date!): Boolean
        }
    """

    def resolve_test(*_, value):
        assert value == date.today()
        return True

    def parse_literal(ast):
        if isinstance(ast, StringValue):
            formatted_date = ast.value
            parsed_datetime = datetime.strptime(formatted_date, "%Y-%m-%d")
            return parsed_datetime.date()
        return None

    resolvers = {
        "Query": {"test": resolve_test},
        "Date": {"parse_literal": parse_literal},
    }

    schema = make_executable_schema(type_defs, resolvers)

    test_input = date.today().strftime("%Y-%m-%d")
    result = graphql(schema, '{ test(value: "%s") }' % test_input)
    assert result.errors is None
    assert result.data == {"test": True}
