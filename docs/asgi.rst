ASGI app
========

.. module:: ariadne.asgi

Ariadne provides a :py:class:`GraphQL` class that implements a production-ready ASGI application.


Using with an ASGI server
-------------------------

First create an application instance pointing it to the schema to serve::

    # in myasgi.py
    import os

    from ariadne import make_executable_schema
    from ariadne.asgi import GraphQL
    from mygraphql import type_defs, resolvers

    schema = make_executable_schema(type_defs, resolvers)
    application = GraphQL(schema)

Then point an ASGI server such as uvicorn at the above instance.

Example using uvicorn::

    $ uvicorn myasgi:application


Customizing context or root
---------------------------

:py:class:`GraphQL` defines two methods that you can redefine in inheriting classes:

.. method:: GraphQL.root_value_for_document(query, variables)

    :param query: `DocumentNode` representing the query sent by the client.
    :param variables: an optional `dict` representing the query variables.
    :return: value that should be passed to root resolvers as the parent (first argument).

.. method:: GraphQL.context_for_request(request)

    :param request: either a `Request` sent by the client or a message sent over a `WebSocket`.
    :return: value that should be passed to resolvers as ``context`` attribute on the ``info`` argument.

The following example shows custom a GraphQL server that defines its own root and context::

    from ariadne.asgi import GraphQL:
    from . import DataLoader, MyContext


    class MyGraphQL(GraphQL):
        def root_value_for_document(self, query, variables):
            return DataLoader()

        def context_for_request(self, request):
            return MyContext(request)
