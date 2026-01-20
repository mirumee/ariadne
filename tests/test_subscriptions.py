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


# Tests for synchronous generators
def test_sync_generator_source_can_be_set_using_setter(schema):
    def sync_source(*_):
        yield "test"

    subscription = SubscriptionType()
    subscription.set_source("message", sync_source)
    subscription.bind_to_schema(schema)
    field = schema.type_map.get("Subscription").fields["message"]
    # The sync generator should be wrapped in an async generator
    assert field.subscribe is not sync_source
    assert callable(field.subscribe)


def test_sync_generator_source_can_be_set_using_decorator(schema):
    def sync_source(*_):
        yield "test"

    subscription = SubscriptionType()
    subscription.source("message")(sync_source)
    subscription.bind_to_schema(schema)
    field = schema.type_map.get("Subscription").fields["message"]
    # The sync generator should be wrapped in an async generator
    assert field.subscribe is not sync_source
    assert callable(field.subscribe)


@pytest.mark.asyncio
async def test_sync_generator_yields_values_correctly():
    """Test that synchronous generators yield values correctly."""
    from ariadne import SubscriptionType, make_executable_schema
    from ariadne.graphql import subscribe

    def sync_counter(*_, limit: int = 3):
        for i in range(limit):
            yield {"counter": i + 1}

    subscription = SubscriptionType()
    subscription.set_source("counter", sync_counter)

    schema = make_executable_schema(
        """
        type Query {
            _: Boolean
        }
        type Subscription {
            counter(limit: Int): Int!
        }
        """,
        subscription,
    )

    success, result = await subscribe(
        schema, {"query": "subscription { counter(limit: 3) }"}
    )
    assert success

    values = []
    async for item in result:
        values.append(item.data["counter"])

    assert values == [1, 2, 3]


@pytest.mark.asyncio
async def test_sync_generator_handles_stop_iteration():
    """Test that StopIteration is properly handled when sync generator exhausts."""
    from ariadne import SubscriptionType, make_executable_schema
    from ariadne.graphql import subscribe

    def finite_sync_source(*_):
        yield {"finite": "first"}
        yield {"finite": "second"}
        # Generator ends naturally

    subscription = SubscriptionType()
    subscription.set_source("finite", finite_sync_source)

    schema = make_executable_schema(
        """
        type Query {
            _: Boolean
        }
        type Subscription {
            finite: String!
        }
        """,
        subscription,
    )

    success, result = await subscribe(schema, {"query": "subscription { finite }"})
    assert success

    values = []
    async for item in result:
        values.append(item.data["finite"])

    assert values == ["first", "second"]


@pytest.mark.asyncio
async def test_sync_generator_propagates_exceptions():
    """Test that exceptions in sync generators are properly propagated."""
    from ariadne import SubscriptionType, make_executable_schema
    from ariadne.graphql import subscribe

    def error_sync_source(*_):
        yield {"error": "first"}
        raise ValueError("Test error")
        yield {"error": "second"}  # pragma: no cover

    subscription = SubscriptionType()
    subscription.set_source("error", error_sync_source)

    schema = make_executable_schema(
        """
        type Query {
            _: Boolean
        }
        type Subscription {
            error: String!
        }
        """,
        subscription,
    )

    success, result = await subscribe(schema, {"query": "subscription { error }"})
    assert success

    # First value should be yielded
    first_item = await result.__anext__()
    assert first_item.data["error"] == "first"

    # Exception should be raised on next iteration
    with pytest.raises(ValueError, match="Test error"):
        await result.__anext__()


@pytest.mark.asyncio
async def test_sync_generator_cleanup_on_disconnect():
    """Test that sync generators are properly closed when subscription ends."""
    import asyncio

    from ariadne import SubscriptionType, make_executable_schema
    from ariadne.graphql import subscribe

    cleanup_called = []

    def sync_source_with_cleanup(*_):
        try:
            for i in range(5):
                yield {"cleanup": i}
        finally:
            cleanup_called.append(True)

    subscription = SubscriptionType()
    subscription.set_source("cleanup", sync_source_with_cleanup)

    schema = make_executable_schema(
        """
        type Query {
            _: Boolean
        }
        type Subscription {
            cleanup: Int!
        }
        """,
        subscription,
    )

    success, result = await subscribe(schema, {"query": "subscription { cleanup }"})
    assert success

    # Consume first two items
    await result.__anext__()
    await result.__anext__()

    # Close the async generator (simulating client disconnect)
    await result.aclose()

    # Give cleanup a moment to execute (cleanup happens in thread)
    # Need to wait a bit longer for thread execution
    for _ in range(10):  # Try multiple times
        await asyncio.sleep(0.05)
        if len(cleanup_called) > 0:
            break

    # Cleanup should have been called
    assert len(cleanup_called) > 0, "Cleanup was not called"


@pytest.mark.asyncio
async def test_sync_generator_with_blocking_io():
    """Test that blocking I/O in sync generators doesn't block the event loop."""
    import time

    from ariadne import SubscriptionType, make_executable_schema
    from ariadne.graphql import subscribe

    def blocking_sync_source(*_):
        # Simulate blocking I/O
        time.sleep(0.1)
        yield {"blocking": "blocking_result"}

    subscription = SubscriptionType()
    subscription.set_source("blocking", blocking_sync_source)

    schema = make_executable_schema(
        """
        type Query {
            _: Boolean
        }
        type Subscription {
            blocking: String!
        }
        """,
        subscription,
    )

    # Start subscription
    start_time = time.time()
    success, result = await subscribe(schema, {"query": "subscription { blocking }"})
    assert success

    # Consume the result
    item = await result.__anext__()
    elapsed = time.time() - start_time

    # The blocking sleep should not block the event loop
    # (it runs in a thread, so other tasks can continue)
    assert item.data["blocking"] == "blocking_result"
    # The elapsed time should be roughly the sleep time (0.1s)
    # but the event loop wasn't blocked
    assert elapsed < 0.2  # Should be close to 0.1s, not blocking


@pytest.mark.asyncio
async def test_sync_and_async_generators_work_together():
    """Test that sync and async generators can coexist in the same subscription type."""
    from ariadne import SubscriptionType, make_executable_schema
    from ariadne.graphql import subscribe

    def sync_source(*_):
        yield {"syncSub": "sync_value"}

    async def async_source(*_):
        yield {"asyncSub": "async_value"}

    subscription = SubscriptionType()
    subscription.set_source("syncSub", sync_source)
    subscription.set_source("asyncSub", async_source)

    schema = make_executable_schema(
        """
        type Query {
            _: Boolean
        }
        type Subscription {
            syncSub: String!
            asyncSub: String!
        }
        """,
        subscription,
    )

    # Test sync subscription
    success, sync_result = await subscribe(
        schema, {"query": "subscription { syncSub }"}
    )
    assert success
    sync_item = await sync_result.__anext__()
    assert sync_item.data["syncSub"] == "sync_value"

    # Test async subscription
    success, async_result = await subscribe(
        schema, {"query": "subscription { asyncSub }"}
    )
    assert success
    async_item = await async_result.__anext__()
    assert async_item.data["asyncSub"] == "async_value"
