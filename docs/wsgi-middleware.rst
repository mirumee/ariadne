WSGI Middleware
===============

.. module:: ariadne

Ariadne provides :py:class:`GraphQLMiddleware` that realizes following goals:

- is production-ready WSGI middleware that can be added to existing setups to start building GraphQL API quickly.
- it's designed to encourage easy customization through extension.
- provides reference implementation for Ariadne GraphQL server.
- implements `make_simple_server` utility for running local development servers without having to setup full-fledged web framework.


Using as Middleware
-------------------

To add GraphQL API to your project using ``GraphQLMiddleware`` instantiate it with your existing WSGI application as first argument, type defs as second and resolvers as third::

    # in wsgi.py
    import os

    from django.core.wsgi import get_wsgi_application
    from ariadne import GraphQLMiddleware
    from mygraphql import type_defs, resolvers

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mydjangoproject.settings")

    django_application = get_wsgi_application()
    application = GraphQLMiddleware(django_application, type_defs, resolvers)

Now direct your WSGI container to `wsgi.application`. GraphQL API is available on ``/graphql/`` by default, but this can be customized by passing path as fourth argument::

    # GraphQL will now be available on "/graphql-v2/" path
    application = GraphQLMiddleware(
        django_application, type_defs, resolvers, "/graphql-v2/"
    )


Customizing context or root
---------------------------

:py:class:`GraphQLMiddleware` defines two methods that you can redefine in inheriting classes:

.. method:: GraphQLMiddleware.get_query_root(environ, request_data)

    :param environ: `dict` representing HTTP request received by WSGI server.
    :param request_data: json that was sent as request body and deserialized to `dict`.
    :return: value that should be passed to root resolvers as first argument.

.. method:: GraphQLMiddleware.get_query_context(environ, request_data)

    :param environ: `dict` representing HTTP request received by WSGI server.
    :param request_data: json that was sent as request body and deserialized to `dict`.
    :return: value that should be passed to resolvers as ``context`` attribute on ``info`` argument.

Following example shows custom GraphQL middleware that defines its own root and context::


    from ariadne import GraphQLMiddleware:
    from . import DataLoader, MyContext


    class MyGraphQLMiddleware(GraphQLMiddleware):
        def get_query_root(self, environ, request_data):
            return DataLoader(environ)

        def get_query_context(self, environ, request_data):
            return MyContext(environ, request_data)


Using simple server
-------------------

:py:class:`GraphQLMiddleware` and inheriting types define class method ``make_simple_server`` with following signature:

.. method:: GraphQLMiddleware.make_simple_server(type_defs, resolvers, host="127.0.0.1", port=8888)

    :param type_defs: `str` or list of `str` with SDL for type definitions.
    :param resolvers: `dict` or list of `dict` with resolvers.
    :param host: `str` of host on which simple server should list.
    :param port: `int` of port on which simple server should run.
    :return: instance of :py:class:`wsgiref.simple_server.WSGIServer` with middleware running as WSGI app handling *all* incoming requests.

The ``make_simple_server`` respects inheritance chain, so you can use it in custom classes inheriting from ``GraphQLMiddleware``::

    from ariadne import GraphQLMiddleware:
    from . import type_defs, resolvers


    class MyGraphQLMiddleware(GraphQLMiddleware):
        def get_query_context(self, environ, request_data):
            return MyContext(environ, request_data)

    simple_server = MyGraphQLMiddleware(type_defs, resolvers)
    simple_server.serve_forever()  # info.context will now be instance of MyContext