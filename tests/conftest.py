import pytest
from graphql.validation.rules import ValidationRule

from ariadne import (
    MutationType,
    QueryType,
    SubscriptionType,
    make_executable_schema,
    upload_scalar,
)


@pytest.fixture
def type_defs():
    return """
        scalar Upload

        type Query {
            hello(name: String): String
            status: Boolean
            testContext: String
            testRoot: String
            testError: Boolean
        }

        type Mutation {
            upload(file: Upload!): String
        }

        type Subscription {
            ping: String!
            resolverError: Boolean
            sourceError: Boolean
            testContext: String
            testRoot: String
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


def resolve_error(*_):
    raise Exception("Test exception")


@pytest.fixture
def resolvers():
    query = QueryType()
    query.set_field("hello", resolve_hello)
    query.set_field("status", resolve_status)
    query.set_field("testContext", resolve_test_context)
    query.set_field("testRoot", resolve_test_root)
    query.set_field("testError", resolve_error)
    return query


def resolve_upload(*_, file):
    if file is not None:
        return type(file).__name__
    return None


@pytest.fixture
def mutations():
    mutation = MutationType()
    mutation.set_field("upload", resolve_upload)
    return mutation


async def ping_generator(*_):
    yield {"ping": "pong"}


async def error_generator(*_):
    raise Exception("Test exception")
    yield 1  # pylint: disable=unreachable


async def test_context_generator(_, info):
    yield {"testContext": info.context.get("test")}


async def test_root_generator(root, *_):
    yield {"testRoot": root.get("test")}


@pytest.fixture
def subscriptions():
    subscription = SubscriptionType()
    subscription.set_source("ping", ping_generator)
    subscription.set_source("resolverError", ping_generator)
    subscription.set_field("resolverError", resolve_error)
    subscription.set_source("sourceError", error_generator)
    subscription.set_source("testContext", test_context_generator)
    subscription.set_source("testRoot", test_root_generator)
    return subscription


@pytest.fixture
def schema(type_defs, resolvers, mutations, subscriptions):
    return make_executable_schema(
        type_defs, [resolvers, mutations, subscriptions, upload_scalar]
    )


@pytest.fixture
def validation_rule():
    class NoopRule(ValidationRule):
        pass

    return NoopRule
