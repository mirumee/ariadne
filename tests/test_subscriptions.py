import pytest
from graphql import build_schema

from ariadne import SubscriptionType


@pytest.fixture
def schema():
    return build_schema(
        """
            type Query {
                hello: String
            }

            type Subscription {
                message: String!
            }
        """
    )


def test_field_source_can_be_set_using_setter(schema):
    async def source(*_):
        yield "test"  # pragma: no cover

    subscription = SubscriptionType()
    subscription.set_source("message", source)
    subscription.bind_to_schema(schema)
    field = schema.type_map.get("Subscription").fields["message"]
    assert field.subscribe is source


def test_field_source_can_be_set_using_decorator(schema):
    async def source(*_):
        yield "test"  # pragma: no cover

    subscription = SubscriptionType()
    subscription.source("message")(source)
    subscription.bind_to_schema(schema)
    field = schema.type_map.get("Subscription").fields["message"]
    assert field.subscribe is source


def test_value_error_is_raised_if_source_decorator_was_used_without_argument():
    async def source(*_):
        yield "test"  # pragma: no cover

    subscription = SubscriptionType()
    with pytest.raises(ValueError):
        subscription.source(source)


def test_attempt_bind_subscription_to_undefined_field_raises_error(schema):
    async def source(*_):
        yield "test"  # pragma: no cover

    subscription = SubscriptionType()
    subscription.set_source("fake", source)
    with pytest.raises(ValueError):
        subscription.bind_to_schema(schema)
