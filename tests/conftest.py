import pytest

from ariadne import ResolverMap, make_executable_schema


@pytest.fixture
def type_defs():
    return """
        type Query {
            hello(name: String): String
            status: Boolean
        }
    """


def resolve_hello(*_, name):
    return "Hello, %s!" % name


def resolve_status(*_):
    return True


@pytest.fixture
def resolvers():
    query = ResolverMap("Query")
    query.field("hello")(resolve_hello)
    query.field("status")(resolve_status)
    return query


@pytest.fixture
def schema(type_defs, resolvers):
    return make_executable_schema(type_defs, resolvers)
