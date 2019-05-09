import pytest

from ariadne import QueryType, SubscriptionType, make_executable_schema


@pytest.fixture
def type_defs():
    return """
        type Query {
            hello(name: String): String
            status: Boolean
            testContext: String
            testRoot: String 
        }

        type Subscription {
            ping: String!
        }
    """


def resolve_hello(*_, name):
    return "Hello, %s!" % name


def resolve_status(*_):
    return True


def resolve_test_context(_, info):
    return info.context.get("test")


def resolve_test_root(root, *_):
    return root.get("test")


@pytest.fixture
def resolvers():
    query = QueryType()
    query.set_field("hello", resolve_hello)
    query.set_field("status", resolve_status)
    query.set_field("testContext", resolve_test_context)
    query.set_field("testRoot", resolve_test_root)
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
