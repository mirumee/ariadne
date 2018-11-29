from graphql import graphql_sync

from ariadne import ResolverMap, make_executable_schema

enum_definition = """
    enum Episode {
        NEWHOPE
        EMPIRE
        JEDI
    }
"""

enum_field = """
    type Query {
        testEnum: Episode!
    }
"""

TEST_VALUE = "NEWHOPE"
INVALID_VALUE = "LUKE"


def test_succesfull_enum_typed_field():
    query = ResolverMap("Query")
    query.field("testEnum")(lambda *_: TEST_VALUE)

    schema = make_executable_schema([enum_definition, enum_field], query)
    result = graphql_sync(schema, "{ testEnum }")
    assert result.errors is None


def test_unsuccesfull_invalid_enum_value_evaluation():
    query = ResolverMap("Query")
    query.field("testEnum")(lambda *_: INVALID_VALUE)

    schema = make_executable_schema([enum_definition, enum_field], query)
    result = graphql_sync(schema, "{ testEnum }")
    assert result.errors is not None


enum_param = """
    type Query {
        testEnum(value: Episode!): Boolean!
    }
"""


def test_succesfull_enum_value_passed_as_argument():
    query = ResolverMap("Query")
    query.field("testEnum")(lambda *_, value: True)

    schema = make_executable_schema([enum_definition, enum_param], query)
    result = graphql_sync(schema, "{ testEnum(value: %s) }" % TEST_VALUE)
    assert result.errors is None, result.errors


def test_unsuccesfull_invalid_enum_value_passed_as_argument():
    query = ResolverMap("Query")
    query.field("testEnum")(lambda *_, value: True)

    schema = make_executable_schema([enum_definition, enum_param], query)
    result = graphql_sync(schema, "{ testEnum(value: %s) }" % INVALID_VALUE)
    assert result.errors is not None
