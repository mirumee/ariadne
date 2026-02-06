"""Tests for subscription events."""

from graphql import ExecutionResult, GraphQLError

from ariadne.subscription_handlers.events import (
    SubscriptionEvent,
    SubscriptionEventType,
)


def test_subscription_event_type_values():
    """Test that SubscriptionEventType has expected values."""
    assert SubscriptionEventType.NEXT.value == "next"
    assert SubscriptionEventType.ERROR.value == "error"
    assert SubscriptionEventType.COMPLETE.value == "complete"
    assert SubscriptionEventType.KEEP_ALIVE.value == "keep_alive"


def test_subscription_event_next_creation():
    """Test creating a NEXT SubscriptionEvent."""
    result = ExecutionResult(data={"hello": "world"})
    event = SubscriptionEvent(
        event_type=SubscriptionEventType.NEXT,
        result=result,
    )

    assert event.event_type == SubscriptionEventType.NEXT
    assert event.result == result
    assert event.result.data == {"hello": "world"}


def test_subscription_event_error_creation():
    """Test creating an ERROR SubscriptionEvent."""
    result = ExecutionResult(errors=[GraphQLError("Test error")])
    event = SubscriptionEvent(
        event_type=SubscriptionEventType.ERROR,
        result=result,
    )

    assert event.event_type == SubscriptionEventType.ERROR
    assert event.result == result
    assert len(event.result.errors) == 1
    assert event.result.errors[0].message == "Test error"


def test_subscription_event_complete_creation():
    """Test creating a COMPLETE SubscriptionEvent."""
    event = SubscriptionEvent(event_type=SubscriptionEventType.COMPLETE)

    assert event.event_type == SubscriptionEventType.COMPLETE
    assert event.result is None


def test_subscription_event_keep_alive_creation():
    """Test creating a KEEP_ALIVE SubscriptionEvent."""
    event = SubscriptionEvent(event_type=SubscriptionEventType.KEEP_ALIVE)

    assert event.event_type == SubscriptionEventType.KEEP_ALIVE
    assert event.result is None


def test_subscription_event_type_has_all_members():
    """Test that SubscriptionEventType has expected enum members."""
    expected = {"next", "error", "complete", "keep_alive"}
    actual = {e.value for e in SubscriptionEventType}
    assert actual == expected


def test_subscription_event_default_result_none():
    """Test that SubscriptionEvent defaults result to None."""
    complete_event = SubscriptionEvent(event_type=SubscriptionEventType.COMPLETE)
    keep_alive_event = SubscriptionEvent(event_type=SubscriptionEventType.KEEP_ALIVE)

    assert complete_event.result is None
    assert keep_alive_event.result is None
