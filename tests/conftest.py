import pytest

from ariadne import QueryType, SubscriptionType, make_executable_schema


@pytest.fixture
def type_defs():
    return """
        type Query {
            hello(name: String): String
            status: Boolean
        }

        type Subscription {
            ping: String!
        }
    """


def resolve_hello(*_, name):
    return "Hello, %s!" % name


def resolve_status(*_):
    return True


@pytest.fixture
def resolvers():
    query = QueryType()
    query.field("hello")(resolve_hello)
    query.field("status")(resolve_status)
    return query


async def ping(*_):
    yield {"ping": "pong"}


@pytest.fixture
def subscriptions():
    subs = SubscriptionType()
    subs.source("ping")(ping)
    return subs


@pytest.fixture
def schema(type_defs, resolvers, subscriptions):
    return make_executable_schema(type_defs, [resolvers, subscriptions])
