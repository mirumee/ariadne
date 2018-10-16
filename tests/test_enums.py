from graphql import graphql
from ariadne import make_executable_schema

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


def test_succesfull_enum():
    resolvers = {"Query": {"testEnum": lambda *_: TEST_VALUE}}
    schema = make_executable_schema([enum_definition, enum_field], resolvers)
    result = graphql(schema, "{ testEnum }")
    assert result.errors is None


def test_failed_enum():
    resolvers = {"Query": {"testEnum": lambda *_: INVALID_VALUE}}
    schema = make_executable_schema([enum_definition, enum_field], resolvers)
    result = graphql(schema, "{ testEnum }")
    assert result.errors is not None


enum_param = """
    type Query {
        testEnum(value: Episode!): Boolean!
    }
"""


def test_enum_as_param():
    resolvers = {"Query": {"testEnum": lambda *_, value: True}}
    schema = make_executable_schema([enum_definition, enum_param], resolvers)
    result = graphql(schema, "{ testEnum(value: %s) }" % TEST_VALUE)
    assert result.errors is None, result.errors


def test_invalid_enum_parameter():
    resolvers = {"Query": {"testEnum": lambda *_, value: True}}
    schema = make_executable_schema([enum_definition, enum_param], resolvers)
    result = graphql(schema, "{ testEnum(value: %s) }" % INVALID_VALUE)
    assert result.errors is not None
