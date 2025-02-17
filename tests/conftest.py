import asyncio
from collections.abc import Mapping

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
            context: String
        }

        type Mutation {
            upload(file: Upload!): String
            echo(text: String!): String
        }

        type Subscription {
            ping: String!
            resolverError: Boolean
            sourceError: Boolean
            testContext: String
            testRoot: String
            testSlow: String
        }
    """


def resolve_hello(*_, name):
    return f"Hello, {name}!"


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


async def async_resolve_hello(*_, name):
    return f"Hello, {name}!"


async def async_resolve_status(*_):
    return True


async def async_resolve_test_context(_, info):
    return info.context.get("test")


async def async_resolve_test_root(root, *_):
    return root.get("test")


async def async_resolve_error(*_):
    raise Exception("Test exception")


@pytest.fixture
def async_resolvers():
    query = QueryType()
    query.set_field("hello", async_resolve_hello)
    query.set_field("status", async_resolve_status)
    query.set_field("testContext", async_resolve_test_context)
    query.set_field("testRoot", async_resolve_test_root)
    query.set_field("testError", async_resolve_error)
    return query


def combined_resolve_hello(*args, **kwargs):
    return async_resolve_hello(*args, **kwargs)


def combined_resolve_status(*args, **kwargs):
    return async_resolve_status(*args, **kwargs)


def combined_resolve_test_context(*args, **kwargs):
    return async_resolve_test_context(*args, **kwargs)


def combined_resolve_test_root(*args, **kwargs):
    return async_resolve_test_root(*args, **kwargs)


def combined_resolve_error(*args, **kwargs):
    return async_resolve_error(*args, **kwargs)


@pytest.fixture
def combined_resolvers():
    query = QueryType()
    query.set_field("hello", combined_resolve_hello)
    query.set_field("status", combined_resolve_status)
    query.set_field("testContext", combined_resolve_test_context)
    query.set_field("testRoot", combined_resolve_test_root)
    query.set_field("testError", combined_resolve_error)
    return query


def resolve_upload(*_, file):
    if file is not None:
        return type(file).__name__
    return None


def resolve_echo(*_, text):
    return f"Echo: {text}"


@pytest.fixture
def mutations():
    mutation = MutationType()
    mutation.set_field("upload", resolve_upload)
    mutation.set_field("echo", resolve_echo)
    return mutation


async def ping_generator(*_):
    yield {"ping": "pong"}


async def error_generator(*_):
    raise Exception("Test exception")
    yield 1


async def test_context_generator(_, info):
    yield {"testContext": info.context.get("test")}


async def test_root_generator(root, *_):
    yield {"testRoot": root.get("test")}


async def test_slow_generator(*_):
    yield {"testSlow": "slow"}
    await asyncio.sleep(20)
    yield {"testSlow": "slow"}


@pytest.fixture
def subscriptions():
    subscription = SubscriptionType()
    subscription.set_source("ping", ping_generator)
    subscription.set_source("resolverError", ping_generator)
    subscription.set_field("resolverError", resolve_error)
    subscription.set_source("sourceError", error_generator)
    subscription.set_source("testContext", test_context_generator)
    subscription.set_source("testRoot", test_root_generator)
    subscription.set_source("testSlow", test_slow_generator)
    return subscription


@pytest.fixture
def schema(type_defs, resolvers, mutations, subscriptions):
    # Schema with synchronous resolvers
    return make_executable_schema(
        type_defs, [resolvers, mutations, subscriptions, upload_scalar]
    )


@pytest.fixture
def async_schema(type_defs, async_resolvers, mutations, subscriptions):
    # Schema with asynchronous resolvers
    return make_executable_schema(
        type_defs, [async_resolvers, mutations, subscriptions, upload_scalar]
    )


@pytest.fixture
def combined_schema(type_defs, combined_resolvers, mutations, subscriptions):
    # Schema with synchronous resolvers returning awaitables
    return make_executable_schema(
        type_defs, [combined_resolvers, mutations, subscriptions, upload_scalar]
    )


@pytest.fixture
def validation_rule():
    class NoopRule(ValidationRule):
        pass

    return NoopRule


@pytest.fixture
def fake_mapping():
    class FakeMapping(Mapping):
        def __init__(self, **kwargs):
            self._dummy = {**kwargs}

        def __getitem__(self, key):
            return self._dummy[key]

        def __iter__(self):
            return iter(self._dummy)

        def __len__(self):
            return len(self._dummy.keys())

    return FakeMapping
