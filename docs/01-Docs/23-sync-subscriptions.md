# Synchronous Generator Subscriptions

Ariadne supports both **asynchronous** and **synchronous** generators as subscription sources. Synchronous generators are automatically executed in worker threads to avoid blocking the event loop, making it easy to integrate blocking I/O operations (like database queries, file operations, or third-party APIs) into GraphQL subscriptions.

## Table of Contents

- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Use Cases](#use-cases)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Technical Details](#technical-details)

## Quick Start

### Basic Synchronous Generator

```python
from ariadne import SubscriptionType, make_executable_schema

subscription = SubscriptionType()

@subscription.source("messages")
def message_source(*_, channel: str = "default"):
    # This is a synchronous generator - no async/await needed!
    for message in get_messages_from_database(channel):  # Blocking DB call
        yield {"text": message.text, "author": message.author}

schema = make_executable_schema(
    """
    type Query {
        _: Boolean
    }
    type Subscription {
        messages(channel: String): Message!
    }
    type Message {
        text: String!
        author: String!
    }
    """,
    subscription,
)
```

### Comparison: Async vs Sync

**Async Generator (existing approach):**
```python
@subscription.source("messages")
async def message_source(*_, channel: str = "default"):
    async for message in async_db_client.stream_messages(channel):
        yield {"text": message.text, "author": message.author}
```

**Sync Generator (new approach):**
```python
@subscription.source("messages")
def message_source(*_, channel: str = "default"):
    for message in sync_db_client.get_messages(channel):  # Blocking call
        yield {"text": message.text, "author": message.author}
```

Both work identically from the client's perspective!

## How It Works

### Automatic Detection

When you register a subscription source, Ariadne automatically detects whether it's synchronous or asynchronous:

- **Async generators**: Functions defined with `async def` that use `yield`
- **Synchronous generators**: Functions defined with `def` that use `yield`

### Thread Offloading

Synchronous generators are automatically wrapped in an async generator that:

1. **Creates the sync generator** when the subscription starts
2. **Executes `next(gen)` calls in a worker thread** using `anyio.to_thread.run_sync()` (or `asyncio.to_thread()` as fallback)
3. **Yields values** from the sync generator to the async stream
4. **Handles cleanup** by calling `gen.close()` when the subscription ends or client disconnects

### Flow Diagram

```
Client Request
    ↓
GraphQL Subscription Execution
    ↓
Is source sync or async?
    ├─→ Async: Execute directly
    └─→ Sync: Wrap in async generator
              ↓
         Worker Thread Pool
              ↓
         Execute next(sync_gen)
              ↓
         Yield value to async stream
              ↓
         Client receives update
```

## Use Cases

### 1. Legacy Database Integrations

When working with synchronous database libraries (like `psycopg2`, `pymongo`, or Django ORM):

```python
from django.db import models

@subscription.source("posts")
def post_updates(*_, category: str = None):
    # Django ORM queries are synchronous
    queryset = models.Post.objects.filter(category=category)
    
    for post in queryset.iterator():
        yield {
            "id": post.id,
            "title": post.title,
            "content": post.content,
        }
```

### 2. File System Monitoring

```python
import os
import time

@subscription.source("fileChanges")
def watch_file(*_, filepath: str):
    last_modified = 0
    
    while True:
        try:
            current_modified = os.path.getmtime(filepath)
            if current_modified > last_modified:
                last_modified = current_modified
                with open(filepath, 'r') as f:
                    yield {"content": f.read(), "modified": current_modified}
            time.sleep(1)  # Blocking sleep is OK!
        except FileNotFoundError:
            break
```

### 3. Third-Party API Polling

```python
import requests

@subscription.source("apiUpdates")
def poll_api(*_, endpoint: str):
    while True:
        response = requests.get(endpoint)  # Blocking HTTP call
        yield {"data": response.json(), "status": response.status_code}
        time.sleep(5)  # Poll every 5 seconds
```

### 4. Message Queue Consumers

```python
import pika  # RabbitMQ synchronous client

@subscription.source("queueMessages")
def consume_queue(*_, queue_name: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    try:
        for method, properties, body in channel.consume(queue_name):
            if body:
                yield {"message": body.decode(), "routing_key": method.routing_key}
                channel.basic_ack(method.delivery_tag)
    finally:
        connection.close()  # Cleanup happens automatically!
```

## Examples

### Example 1: Database Query Stream

```python
from ariadne import SubscriptionType, make_executable_schema
import sqlite3

subscription = SubscriptionType()

@subscription.source("users")
def user_stream(*_, active: bool = True):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        query = "SELECT id, name, email FROM users WHERE active = ?"
        cursor.execute(query, (active,))
        
        for row in cursor:
            yield {
                "id": row[0],
                "name": row[1],
                "email": row[2],
            }
    finally:
        conn.close()  # Cleanup in finally block

@subscription.field("users")
def resolve_user(message, *_):
    return message  # Pass through the yielded data

schema = make_executable_schema(
    """
    type Query {
        _: Boolean
    }
    type Subscription {
        users(active: Boolean): User!
    }
    type User {
        id: ID!
        name: String!
        email: String!
    }
    """,
    subscription,
)
```

### Example 2: Time-Based Events

```python
import time
from datetime import datetime

@subscription.source("timeUpdates")
def time_stream(*_, interval: int = 1):
    """Emit current time at specified intervals."""
    while True:
        yield {
            "timestamp": datetime.now().isoformat(),
            "unix_time": int(time.time()),
        }
        time.sleep(interval)  # Blocking sleep

@subscription.field("timeUpdates")
def resolve_time(message, *_):
    return message
```

### Example 3: Mixed Sync/Async Sources

You can mix synchronous and asynchronous generators in the same subscription type:

```python
subscription = SubscriptionType()

# Sync source for blocking operations
@subscription.source("syncData")
def sync_source(*_):
    # Blocking I/O
    data = requests.get("https://api.example.com/data").json()
    yield data

# Async source for async operations
@subscription.source("asyncData")
async def async_source(*_):
    # Non-blocking I/O
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/data") as resp:
            data = await resp.json()
            yield data
```

## Best Practices

### 1. Resource Cleanup

Always use `try...finally` blocks for cleanup in synchronous generators:

```python
@subscription.source("data")
def data_source(*_):
    connection = create_connection()
    try:
        for item in connection.stream():
            yield item
    finally:
        connection.close()  # Always cleanup
```

**Note**: Ariadne automatically calls `gen.close()` when the subscription ends, which triggers the `finally` block.

### 2. Error Handling

Handle exceptions appropriately:

```python
@subscription.source("data")
def data_source(*_):
    try:
        for item in get_data():
            yield item
    except ConnectionError as e:
        # Log error, yield error message, or re-raise
        yield {"error": str(e)}
        raise  # Re-raise to propagate to GraphQL error handling
```

### 3. Generator Exhaustion

Synchronous generators can exhaust naturally:

```python
@subscription.source("limited")
def limited_source(*_, count: int = 10):
    for i in range(count):
        yield {"value": i}
    # Generator ends naturally - no need to raise StopIteration
```

### 4. Performance Considerations

- **Use sync generators** for: Legacy libraries, blocking I/O, CPU-bound operations
- **Use async generators** for: Modern async libraries, high-concurrency scenarios
- **Thread pool**: Sync generators share a thread pool, so avoid creating too many concurrent subscriptions with blocking operations

### 5. Scalability Considerations

**Important**: Synchronous generators are implemented using thread-based execution (`anyio.to_thread.run_sync` or `asyncio.to_thread`). This approach has scalability implications that should be understood:

#### Thread Pool Limitations

- **Limited concurrent subscriptions**: The number of concurrent synchronous subscriptions is bounded by the thread pool size (typically 32-40 threads by default, depending on Python version and runtime)
- **Thread pool exhaustion**: If you exceed the thread pool capacity, new subscription requests will wait for available threads, potentially causing delays or timeouts

#### Memory Overhead

- **Higher memory usage**: Each synchronous subscription consumes:
  - Thread stack space (~8MB per thread on most systems)
  - Generator state and context
  - Any resources held by the synchronous generator (database connections, file handles, etc.)
- **Memory scaling**: Memory usage scales linearly with the number of concurrent sync subscriptions, unlike async generators which share the event loop

#### Performance Overhead

- **Thread context switching**: Each `next()` call requires:
  - Switching from async context to thread context
  - Executing in a worker thread
  - Switching back to async context
- **Overhead per yield**: This context switching adds latency compared to async generators, which execute directly in the event loop
- **Blocking operations**: While blocking operations don't block the event loop, they still consume thread resources and can impact overall throughput

#### Recommendations

- **For high-concurrency scenarios**: Prefer async generators when possible
- **For legacy integrations**: Sync generators are acceptable for occasional or low-volume subscriptions
- **Monitor thread pool usage**: Watch for thread pool exhaustion warnings in production
- **Consider connection pooling**: If using sync generators with databases, use connection pooling to limit resource consumption
- **Batch operations**: When possible, batch operations in sync generators to reduce the number of thread switches

#### When to Use Each Approach

**Use Async Generators when:**
- You need high concurrency (hundreds or thousands of concurrent subscriptions)
- You have async libraries available (aiohttp, asyncpg, etc.)
- Low latency is critical
- You're building new features from scratch

**Use Sync Generators when:**
- You're integrating with legacy/synchronous libraries
- You have a small number of concurrent subscriptions (< 50)
- Blocking I/O is unavoidable
- You're migrating existing sync code to GraphQL subscriptions
- The convenience of sync code outweighs scalability concerns

### 6. Testing

Test synchronous generators like any other subscription:

```python
import pytest
from ariadne.graphql import subscribe

@pytest.mark.asyncio
async def test_sync_subscription(schema):
    success, result = await subscribe(
        schema, {"query": "subscription { messages { text } }"}
    )
    assert success
    
    # Consume the async generator
    item = await result.__anext__()
    assert item.data["messages"]["text"] == "Hello"
```

## Technical Details

### Thread Safety

- Each synchronous generator runs in its own worker thread
- The `next()` calls are serialized per generator (one at a time)
- Multiple subscriptions can run concurrently in different threads

### Cleanup Mechanism

When a subscription ends (client disconnects, generator exhausts, or error occurs):

1. The async wrapper's `finally` block executes
2. `gen.close()` is called on the synchronous generator in a worker thread
3. This triggers the generator's `finally` block (if present)
4. Resources are cleaned up properly

### Exception Propagation

Exceptions raised in synchronous generators:

1. Are caught by the thread executor
2. Propagated back to the async wrapper
3. Raised in the async generator
4. Handled by GraphQL's error reporting mechanism

### Implementation Details

The wrapping logic:

```python
# Simplified version of what happens internally
async def async_wrapper(*args, **kwargs):
    sync_gen = sync_generator_function(*args, **kwargs)
    
    try:
        while True:
            try:
                # Run next() in worker thread
                value = await to_thread.run_sync(next, sync_gen)
                yield value
            except StopIteration:
                break
    finally:
        # Cleanup: close the sync generator
        if hasattr(sync_gen, "close"):
            await to_thread.run_sync(sync_gen.close)
```

### Compatibility

- **Python**: 3.10+ (uses `asyncio.to_thread` or `anyio.to_thread.run_sync`)
- **Frameworks**: Works with Starlette, FastAPI, and any ASGI-compatible framework
- **Backward Compatible**: Existing async generators continue to work unchanged

## Migration Guide

### From Async to Sync (when needed)

If you have blocking I/O and want to simplify:

**Before:**
```python
@subscription.source("data")
async def data_source(*_):
    # Had to wrap sync calls in run_in_executor
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, blocking_function)
    yield data
```

**After:**
```python
@subscription.source("data")
def data_source(*_):
    # Direct blocking call - Ariadne handles threading
    data = blocking_function()
    yield data
```

### When to Use Each

**Use Async Generators when:**
- You have async libraries available (aiohttp, asyncpg, etc.)
- You need high concurrency
- You're already in an async context

**Use Sync Generators when:**
- You have legacy/synchronous libraries
- Blocking I/O is unavoidable
- You want simpler code without async/await complexity
- You're migrating existing sync code to GraphQL subscriptions

## Troubleshooting

### Generator Not Closing

If your generator's cleanup code isn't running:

1. Ensure you're using `try...finally` blocks
2. Check that `gen.close()` is being called (Ariadne does this automatically)
3. Verify the subscription is properly ending (not hanging)

### Thread Pool Exhaustion

If you see thread pool errors:

- Reduce the number of concurrent sync subscriptions
- Consider converting some to async generators
- Increase thread pool size (framework-dependent)

### Performance Issues

If sync subscriptions are slow:

- Verify blocking operations are necessary
- Consider caching or batching
- Profile to identify bottlenecks
- Consider async alternatives if available

## Summary

Synchronous generator subscriptions provide a simple way to integrate blocking I/O operations into GraphQL subscriptions without requiring async/await complexity. Ariadne automatically handles thread offloading, cleanup, and error propagation, making it easy to work with legacy libraries and blocking operations while maintaining the benefits of async GraphQL subscriptions.
