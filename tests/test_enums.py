from ariadne import make_executable_schema
from graphql import graphql

type_defs = """
    enum Episode {
        NEWHOPE
        EMPIRE
        JEDI
    }

    type Query {
        testEnum: Episode!
    }
"""


def resolve_test_enum(*_):
    return "NEWHOPE"


def test_succesfull_enum():
    resolvers = {"Query": {"testEnum": resolve_test_enum}}
    schema = make_executable_schema(type_defs, resolvers)
    result = graphql(schema, "{ testEnum }")
    assert result.errors is None


def test_failed_enum():
    resolvers = {"Query": {"testEnum": lambda *_: "LUKE"}}
    schema = make_executable_schema(type_defs, resolvers)
    result = graphql(schema, "{ testEnum }")
    assert result.errors is not None
