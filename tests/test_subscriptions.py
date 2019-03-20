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

    sub = SubscriptionType()
    sub.set_source("message", source)
    sub.bind_to_schema(schema)
    field = schema.type_map.get("Subscription").fields["message"]
    assert field.subscribe is source


def test_field_source_can_be_set_using_decorator(schema):
    async def source(*_):
        yield "test"  # pragma: no cover

    sub = SubscriptionType()
    sub.source("message")(source)
    sub.bind_to_schema(schema)
    field = schema.type_map.get("Subscription").fields["message"]
    assert field.subscribe is source


def test_attempt_bind_subscription_to_undefined_field_raises_error(schema):
    async def source(*_):
        yield "test"  # pragma: no cover

    sub_map = SubscriptionType()
    sub_map.set_source("fake", source)
    with pytest.raises(ValueError):
        sub_map.bind_to_schema(schema)
