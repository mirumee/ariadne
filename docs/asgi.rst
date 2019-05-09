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

You can customize context value passed to your resolves using ``context_value`` option::

    app = GraphQL(schema, context_value=CUSTOM_CONTEXT_VALUE)

``context_value`` option accepts value of any type. If type is ``callable`` it will be called with one argument: request representation specific to your HTTP stack, and its return value will then be used as final context value::

    def get_context_value(request):
        return {"user": request.user, "conf": request.conf}

    app = GraphQL(schema, context_value=get_context_value)

To set custom root value passed as parent to root resolvers (resolvers defined on ``Query``, ``Mutation`` and ``Subscribe`` types) ``root_value``::

    app = GraphQL(schema, root_value=CUSTOM_ROOT_VALUE)

``root_value`` option accepts value of any type. If type is ``callable`` it will be called with two arguments: ``context`` and ``document`` that is currently executed query already parsed to ``DocumentNode``. Its return value will then be used as final root value::

    def get_root_value(context, document):
        return {"user": context["user"]}

    app = GraphQL(schema, root_value=get_root_value)