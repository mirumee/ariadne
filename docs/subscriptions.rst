Subscriptions
=============

Let's introduce a third type of operation. While queries offer a way to query a server once, subscriptions offer a way for the server to notify the client each time new data is available and that no other data will be available for the given request.

This is where the ``Subscription`` type comes useful. It's similar to ``Query`` but as each subscription remains an open channel you can send anywhere from zero to millions of responses over its lifetime.

.. warning::
   Because of their nature, subscriptions are only possible to implement in asynchronous servers that implement the WebSockets protocol.
   
   *WSGI*-based servers (including Django) are synchronous in nature and *unable* to handle WebSockets which makes them incapable of implementing subscriptions.

   If you wish to use subscriptions with Django, consider wrapping your Django application in a Django Channels container and using Ariadne as an *ASGI* server.


Defining subscriptions
----------------------

In schema definition subscriptions look similar to queries::

    type_def = """
        type Query {}

        type Subscription {
            counter: Int!
        }
    """

This example contains:

The ``Query`` type with no fields. Ariadne requires you to always have a ``Query`` type.

The ``Subscription`` type with a single field: ``counter`` that returns a number.

When defining subscriptions you can use all of the features of the schema such as arguments, input and output types.


Writing subscriptions
---------------------

Subscriptions are more complex than queries as they require us to provide two functions for each field:

A ``generator`` is a function that yields data we're going to send to the client. It has to implement the ``AsyncGenerator`` protocol.

A ``resolver`` that tells the server how to send data to the client. This is similar to the ref:`resolvers we wrote earlier <resolvers>`.

.. note::
   Make sure you understand how asynchronous generators work before attempting to use subscriptions.

The signatures are as follows::

    async def counter_generator(
        obj: Any, info: GraphQLResolveInfo
    ) -> AsyncGenerator[int, None]:
        for i in range(5):
            await asyncio.sleep(1)
            yield i

    def counter_resolver(
        count: int, info: GraphQLResolveInfo
    ) -> int:
        return count + 1

Note that the resolver consumes the same type (in this case ``int``) that the generator yields.

Each time our source yields a response, its getting sent to our resolver. The above implementation counts from zero to four, each time waiting for one second before yielding a value.

The resolver increases each number by one before passing them to the client so the client sees the counter progress from one to five.

After the last value is yielded the generator returns, the server tells the client that no more data will be available, and the subscription is complete.

We can map these functions to subscription fields using the ``ResolverMap`` like we did for queries and mutations::

    from ariadne import ResolverMap
    from . import counter_subscriptions

    sub_map = ResolverMap("Subscription")
    sub_map.field(
        "counter",
        resolver=counter_subscriptions.counter_resolver
    )
    sub_map.source(
        "counter",
        generator=counter_subscriptions.counter_generator
    )
