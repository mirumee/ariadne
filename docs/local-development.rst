Local development
=================

Using the simple server
-----------------------

The simple server function is suitable for non-production work when the goal is to quickly evaluate an API without using complex third-party tools.

.. function:: ariadne.start_simple_server(schema, *, host="127.0.0.1", port=8888, server_class=GraphQL)

    :param schema: `GraphQLSchema` returned by `make_executable_schema`.
    :param host: `str` of host on which simple server should list.
    :param port: `int` of port on which simple server should run.
    :param server_class: a server class to use for the API, should be a subclass of :py:class:`GraphQL`
    :return: None

You can use the ``server_class`` keyword argument to use ``start_simple_server`` with a custom ``GraphQL`` subclass::

    from ariadne import make_executable_schema, start_simple_server
    from ariadne.wsgi import GraphQL
    from . import type_defs, resolvers


    class MyGraphQL(GraphQL):
        def get_query_context(self, environ, request_data):
            return MyContext(environ, request_data)


    schema = make_executable_schema(type_defs, resolvers)
    start_simple_server(schema, server_class=MyGraphQL)

.. warning::
   ``start_simple_server`` is unsuitable for production use. Please use an appropriate WSGI server such as uWSGI or Gunicorn when exposing GraphQL APIs to the outside world.

.. note::
  ``ariadne.start_simple_server`` is actually a simple shortcut that internally creates HTTP server with ``wsgiref.simple_server``, starts it with `serve_forever`, displays instruction message and handles ``KeyboardInterrupt`` gracefully.


