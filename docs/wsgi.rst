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

:py:class:`GraphQL` defines two methods that you can redefine in inheriting classes:

.. method:: GraphQL.get_query_root(environ, request_data)

    :param environ: `dict` representing HTTP request received by WSGI server.
    :param request_data: json that was sent as request body and deserialized to `dict`.
    :return: value that should be passed to root resolvers as first argument.

.. method:: GraphQL.get_query_context(environ, request_data)

    :param environ: `dict` representing HTTP request received by WSGI server.
    :param request_data: json that was sent as request body and deserialized to `dict`.
    :return: value that should be passed to resolvers as ``context`` attribute on ``info`` argument.

The following example shows custom a GraphQL server that defines its own root and context::

    from ariadne.wsgi import GraphQL:
    from . import DataLoader, MyContext


    class MyGraphQL(GraphQL):
        def get_query_root(self, environ, request_data):
            return DataLoader(environ)

        def get_query_context(self, environ, request_data):
            return MyContext(environ, request_data)


Using the middleware
--------------------

To add GraphQL API to your project using ``GraphQLMiddleware``, instantiate it with your existing WSGI application as a first argument and your schema as the second::

    # in wsgi.py
    import os

    from django.core.wsgi import get_wsgi_application
    from ariadne import make_executable_schema
    from ariadne.wsgi import GraphQLMiddleware
    from mygraphql import type_defs, resolvers

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mydjangoproject.settings")

    schema = make_executable_schema(type_defs, resolvers)
    django_application = get_wsgi_application()
    application = GraphQLMiddleware(django_application, schema)

Now direct your WSGI server to `wsgi.application`. The GraphQL API is available on ``/graphql/`` by default but this can be customized by passing a different path as the third argument::

    # GraphQL will now be available on "/graphql-v2/" path
    application = GraphQLMiddleware(django_application, schema, "/graphql-v2/")

To use a custom server subclass together with ``GraphQLMiddleware`` pass your class as the ``server_class`` keyword argument::

    application = GraphQLMiddleware(django_application, schema, "/graphql/", server_class=MyGraphQL)
