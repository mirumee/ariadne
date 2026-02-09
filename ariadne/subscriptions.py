import inspect
from collections.abc import Callable
from typing import Any, cast

try:
    from anyio import to_thread
except ImportError:
    import asyncio

    class _ThreadAdapter:
        @staticmethod
        async def run_sync(func: Callable[..., Any], *args: Any) -> Any:
            return await asyncio.to_thread(func, *args)

    to_thread: _ThreadAdapter = _ThreadAdapter()

from graphql.type import GraphQLSchema

from .objects import ObjectType
from .types import Subscriber


class SubscriptionType(ObjectType):
    """Bindable populating the Subscription type in a GraphQL schema with Python logic.

    Extends `ObjectType`, providing `source` decorator and `set_source` method, used
    to set subscription sources for it's fields.

    # Subscription sources ("subscribers")

    Subscription source is a function that is a generator (async or sync).
    This function is used to subscribe to source of events or messages.
    It can also filter the messages by not yielding them.

    Its signature is same as resolver:

    ```python
    # Async generator (executed directly)
    async def source_fn(root_value: Any, info: GraphQLResolveInfo, **field_args) -> Any:
        yield ...


    # Synchronous generator (executed in a worker thread to avoid blocking)
    def source_fn(root_value: Any, info: GraphQLResolveInfo, **field_args) -> Any:
        yield ...
    ```

    # Subscription resolvers

    Subscription resolvers are called with message returned from the source. Their role
    is to convert this message into Python representation of a type associated with
    subscription's field in GraphQL schema. Its called with message yielded from
    source function as first argument.

    ```python
    def resolver_fn(message: Any, info: GraphQLResolveInfo, **field_args) -> Any:
        return ...
    ```

    # GraphQL arguments

    When subscription field has arguments those arguments values are passed
    to both source and resolver functions.

    # Example source and resolver

    ```python
    from ariadne import SubscriptionType, make_executable_schema
    from broadcast import broadcast

    from .models import Post


    subscription_type = SubscriptionType()


    @subscription_type.source("post")
    async def source_post(*_, category: Optional[str] = None) -> dict:
        async with broadcast.subscribe(channel="NEW_POSTS") as subscriber:
            async for event in subscriber:
                message = json.loads(event.message)
                if not category or message["category"] == category:
                    yield message


    @subscription_type.field("post")
    async def resolve_post(message: dict, *_, category: Optional[str] = None) -> Post:
        return await Post.get_one(id=message["post_id"])
    ```

    # Synchronous generator example

    Synchronous generators are automatically executed in worker threads to avoid
    blocking the event loop. **Note**: This thread-based implementation has
    scalability implications:
    - Limited number of concurrent subscriptions (bounded by thread pool size)
    - Higher memory overhead per subscription (thread stack + generator state)
    - Performance overhead from thread context switching

    For high-concurrency scenarios, prefer async generators when possible.

    ```python
    from ariadne import SubscriptionType, make_executable_schema
    import time

    subscription_type = SubscriptionType()


    @subscription_type.source("timeUpdates")
    def source_time(*_, interval: int = 1) -> dict:
        while True:
            yield {"timestamp": time.time()}
            time.sleep(interval)


    @subscription_type.field("timeUpdates")
    def resolve_time(message: dict, *_) -> dict:
        return message


    schema = make_executable_schema(
        \"\"\"
        type Query {
            _: Boolean
        }
        type Subscription {
            timeUpdates(interval: Int): TimeUpdate!
        }
        type TimeUpdate {
            timestamp: Float!
        }
        \"\"\",
        subscription_type
    )


    schema = make_executable_schema(
        \"\"\"
        type Query {
            \"Valid schema must define the Query type\"
            none: Int
        }

        type Subscription {
            post(category: ID): Post!
        }

        type Post {
            id: ID!
            author: String!
            text: String!
        }
        \"\"\",
        subscription_type
    )
    ```

    # Example chat

    [Ariadne GraphQL Chat Example](https://github.com/mirumee/ariadne-graphql-chat-example)
    is the Github repository with GraphQL chat application, using Redis message backend,
    Broadcaster library for publishing and subscribing to messages and React.js client
    using Apollo-Client subscriptions.
    """

    _subscribers: dict[str, Subscriber]

    def __init__(self) -> None:
        """Initializes the `SubscriptionType` with a GraphQL name set to `Subscription`."""  # noqa: E501
        super().__init__("Subscription")
        self._subscribers = {}

    def source(self, name: str) -> Callable[[Subscriber], Subscriber]:
        """Return a decorator that sets decorated function as a source for named field.

        Wrapper for `create_register_subscriber` that on runtime
        validates `name` to be a string.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        bind decorated source to.
        """
        if not isinstance(name, str):
            raise ValueError(
                'source decorator should be passed a field name: @foo.source("name")'
            )
        return self.create_register_subscriber(name)

    def create_register_subscriber(
        self, name: str
    ) -> Callable[[Subscriber], Subscriber]:
        """Return a decorator that sets decorated function as a source for named field.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        bind decorated source to.

        # Synchronous generators

        If the decorated function is a synchronous generator (`def` + `yield`), it will
        be automatically wrapped in an async generator that executes the sync generator
        in a worker thread to avoid blocking the event loop. The sync generator will
        be properly cleaned up when the subscription ends or client disconnects.

        **Scalability considerations**: Thread-based execution limits concurrent
        subscriptions (bounded by thread pool size), increases memory overhead per
        subscription, and adds performance overhead from thread context switching.
        For high-concurrency scenarios, prefer async generators.
        """

        def register_subscriber(generator: Subscriber) -> Subscriber:
            is_sync_generator = inspect.isgeneratorfunction(
                generator
            ) and not inspect.isasyncgenfunction(generator)

            if is_sync_generator:

                async def async_wrapper(*args, **kwargs):
                    sync_gen = generator(*args, **kwargs)

                    try:
                        while True:
                            try:

                                def get_next(gen: Any) -> Any:
                                    return next(gen)

                                value = await to_thread.run_sync(get_next, sync_gen)
                                yield value
                            except StopIteration:
                                break
                            except RuntimeError as e:
                                if isinstance(
                                    e.__cause__, StopIteration
                                ) or "StopIteration" in str(e):
                                    break
                                raise
                    finally:
                        try:
                            if hasattr(sync_gen, "close"):
                                close_fn = cast(Callable[[], None], sync_gen.close)
                                await to_thread.run_sync(close_fn)
                        except (Exception, GeneratorExit):
                            pass

                wrapped: Subscriber = async_wrapper
                self._subscribers[name] = wrapped
                return wrapped
            else:
                self._subscribers[name] = generator
                return generator

        return register_subscriber

    def set_source(self, name, generator: Subscriber) -> Subscriber:
        """Set a source for the field name.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        set this source for.

        `generator`: a `Subscriber` function to use as an source. Can be either an async
        generator or a synchronous generator. Synchronous generators will be
        automatically wrapped to run in a worker thread.

        **Scalability note**: Sync generators use thread-based execution which limits
        concurrent subscriptions and increases memory/performance overhead compared
        to async generators.
        """
        is_sync_generator = inspect.isgeneratorfunction(
            generator
        ) and not inspect.isasyncgenfunction(generator)

        if is_sync_generator:

            async def async_wrapper(*args, **kwargs):
                sync_gen = generator(*args, **kwargs)

                try:
                    while True:
                        try:

                            def get_next(gen: Any) -> Any:
                                return next(gen)

                            value = await to_thread.run_sync(get_next, sync_gen)
                            yield value
                        except StopIteration:
                            break
                        except RuntimeError as e:
                            if isinstance(
                                e.__cause__, StopIteration
                            ) or "StopIteration" in str(e):
                                break
                            raise
                finally:
                    try:
                        if hasattr(sync_gen, "close"):
                            close_fn = cast(Callable[[], None], sync_gen.close)
                            await to_thread.run_sync(close_fn)
                    except (Exception, GeneratorExit):
                        pass

            wrapped: Subscriber = async_wrapper
            self._subscribers[name] = wrapped
            return wrapped
        else:
            self._subscribers[name] = generator
            return generator

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `SubscriptionType` instance to the instance of GraphQL schema.

        If it has any previously set subscription resolvers or source functions,
        those will be replaced with new ones from this instance.
        """
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        self.bind_resolvers_to_graphql_type(graphql_type)
        self.bind_subscribers_to_graphql_type(graphql_type)

    def bind_subscribers_to_graphql_type(self, graphql_type):
        """Binds this `SubscriptionType` instance's source functions.

        Source functions are set to fields `subscribe` attributes.
        """
        for field, subscriber in self._subscribers.items():
            if field not in graphql_type.fields:
                raise ValueError(f"Field {field} is not defined on type {self.name}")

            graphql_type.fields[field].subscribe = subscriber
