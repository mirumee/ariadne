WSGI app
========

.. module:: ariadne.wsgi

Ariadne provides a :py:class:`GraphQL` class that implements a production-ready WSGI application.

Ariadne also provides :py:class:`GraphQLMiddleware` that allows you to route between a :py:class:`GraphQL` instance and another WSGI app based on the request path.


Using with a WSGI server
------------------------

First create an application instance pointing it to the schema to serve::

    # in mywsgi.py
    import os

    from ariadne import make_executable_schema
    from ariadne.wsgi import GraphQL
    from mygraphql import type_defs, resolvers

    schema = make_executable_schema(type_defs, resolvers)
    application = GraphQL(schema)

Then point a WSGI server such as uWSGI or Gunicorn at the above instance.

Example using Gunicorn::

    $ gunicorn mywsgi::application

Example using uWSGI::

    $ uwsgi --http :8000 --wsgi-file mywsgi


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


Using the middleware
--------------------

To add GraphQL API to your project using ``GraphQLMiddleware``, instantiate it with your existing WSGI application as a first argument and your schema as the second::

    # in wsgi.py
    import os

    from django.core.wsgi import get_wsgi_application
    from ariadne import make_executable_schema
    from ariadne.wsgi import GraphQL, GraphQLMiddleware
    from mygraphql import type_defs, resolvers

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mydjangoproject.settings")

    schema = make_executable_schema(type_defs, resolvers)
    django_application = get_wsgi_application()
    graphql_application = GraphQL(schema)
    application = GraphQLMiddleware(django_application, graphql_application)

Now direct your WSGI server to `wsgi.application`. The GraphQL API is available on ``/graphql/`` by default but this can be customized by passing a different path as the third argument::

    # GraphQL will now be available on "/graphql-v2/" path
    application = GraphQLMiddleware(django_application, graphql_application, "/graphql-v2/")
