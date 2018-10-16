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


def test_succesfull_enum_typed_field():
    resolvers = {"Query": {"testEnum": lambda *_: TEST_VALUE}}
    schema = make_executable_schema([enum_definition, enum_field], resolvers)
    result = graphql(schema, "{ testEnum }")
    assert result.errors is None


def test_unsuccesfull_invalid_enum_value_evaluation():
    resolvers = {"Query": {"testEnum": lambda *_: INVALID_VALUE}}
    schema = make_executable_schema([enum_definition, enum_field], resolvers)
    result = graphql(schema, "{ testEnum }")
    assert result.errors is not None


enum_param = """
    type Query {
        testEnum(value: Episode!): Boolean!
    }
"""


def test_succesfull_enum_value_passed_as_argument():
    resolvers = {"Query": {"testEnum": lambda *_, value: True}}
    schema = make_executable_schema([enum_definition, enum_param], resolvers)
    result = graphql(schema, "{ testEnum(value: %s) }" % TEST_VALUE)
    assert result.errors is None, result.errors


def test_unsuccesfull_invalid_enum_value_passed_as_argument():
    resolvers = {"Query": {"testEnum": lambda *_, value: True}}
    schema = make_executable_schema([enum_definition, enum_param], resolvers)
    result = graphql(schema, "{ testEnum(value: %s) }" % INVALID_VALUE)
    assert result.errors is not None
