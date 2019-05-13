Integrations
============

Ariadne can be used to add GraphQL server to projects developed using other web frameworks like Django or Flask.

Implementation details differ between frameworks, but same steps apply for most of them:

1. Use `ariadne.make_executable_schema` to create executable schema instance.
2. Create view, route or controller (semantics vary between frameworks) that accepts ``GET`` and ``POST`` requests.
3. If request was made with ``GET`` method, return response containing GraphQL Playground's HTML.
4. If request was made with ``POST``, disable any CSRF checks, test that its content type is ``application/json`` then parse its content as JSON. Return ``400 BAD REQUEST`` if this fails.
5. Call ``ariadne.graphql_sync`` with schema, parsed JSON and any other options that are fit for your implementation.
6. ``ariadne.graphql_sync`` returns tuple that has two values: ``boolean`` and ``dict``. Use dict as data for JSON response, and boolean for status code. If boolean is ``true``, set response's status code to ``200``, otherwise it should be ``400``

Ariadne provides special functions that abstract away the query execution boilerplate while providing variety of configuration options at same time:

.. cofunction:: ariadne.graphql(schema, data, [root_value=None, context_value=None, debug=False, validation_rules, error_formatter, middleware], **kwargs)

    :param schema: an executable schema created using `make_executable_schema`
    :param data: decoded input data sent by the client (eg. for POST requests in JSON format, pass in the structure decoded from JSON), exact shape of `data` will depend on the query type and protocol
    :param context_value: the context value passed to all resolvers (it's common for your context to include the request object specific to your web framework)
    :param root_value: the value passed to the root-level resolvers
    :param debug: if `True` will cause the server to include debug information in error responses
    :param validation_rules: optional additional validators (as defined by `graphql.validation.rules`) to run before attempting to execute the query (the standard validators defined by the GraphQL specification are always used and there's no need to provide them here)
    :param error_formatter: an optional custom function to use for formatting errors, the function will be passed two parameters: a `GraphQLError` exception instance, and the value of the `debug` switch
    :param middleware: optional middleware to wrap the resolvers with
    :return: `(success, response)`, a tuple of two values, the success indicator (boolean), and the response to send to the client (will need to be encoded into an appropriate format)

    This function is an asynchronous coroutine so you will need to ``await`` on the returned value.

    .. warning::
        Coroutines will not work under WSGI. If your server uses WSGI (Django and Flask do), use ``graphql_sync`` instead.


.. function:: ariadne.graphql_sync(schema, data, [root_value=None, context_value=None, debug=False, validation_rules, error_formatter, middleware], **kwargs)

    Parameters are the same as those of the ``graphql`` coroutine above but the function is blocking and the result is returned synchronously. Use this function if your site is running under WSGI.


.. cofunction:: ariadne.subscribe(schema, data, [root_value=None, context_value=None, debug=False, validation_rules, error_formatter], **kwargs)

    Parameters are the same as those of the ``graphql`` coroutine except for the ``middleware`` parameter that is not supported.

    This function is an asynchronous coroutine so you will need to ``await`` on the returned value.


Django integration
------------------

Ariadne ships with ``ariadne.contrib.django`` package that provides ``GraphQLView`` wrapping around GraphQL Playground and query execution::

    # Add ariadne.contrib.django to INSTALLED_APPS
    INSTALLED_APPS = [
        ...
        "ariadne.contrib.django",
    ]


    # ...create schema module with executable schema in it...
    from ariadne import QueryType

    type_defs = """
        type Query {
            hello: String!
        }
    """

    query = QueryType()

    @query.field("hello")
    def resolve_hello(*_):
        return "Hello world!"

    schema = make_executable_schema(type_defs, query)


    # ...and include it in your urls.py using GraphQL view:
    from ariadne.contrib.django.views import GraphQLView
    from django.urls import include, path

    from .schema import schema

    urlpatterns = [
        path('index/', views.index, name='main-view'),
        path('graphql/', GraphQLView.as_view(schema=schema), name='graphql'),
        ...
    ]

``GraphQLView.as_view()`` accepts mostly the same options that ``ariadne.graphql`` described above does. It doesn't accept the ``data`` and ``debug`` because those depend on request and ``settings.DEBUG`` respectively.

For convenience ``ariadne.contrib.django.scalars`` module is also provided that implements ``Date`` and ``DateTime`` scalars::

    from ariadne.contrib.django.scalars import date_scalar, datetime_scalar

    type_defs = """
        scalar Date
        scalar DateTime

        type Query {
            hello: String
        }
    """

    schema = make_executable_schema(type_defs, [date_scalar, datetime_scalar, ...])

Scalars have dependency on `dateutil library <https://github.com/dateutil/dateutil>`_.


Flask integration
-----------------

The following example presents a basic GraphQL server built with Flask::

    from ariadne import QueryType, graphql_sync, make_executable_schema
    from ariadne.constants import PLAYGROUND_HTML
    from flask import Flask, request, jsonify

    type_defs = """
        type Query {
            hello: String!
        }
    """

    query = QueryType()


    @query.field("hello")
    def resolve_hello(_, info):
        request = info.context
        user_agent = request.headers.get("User-Agent", "Guest")
        return "Hello, %s!" % user_agent


    schema = make_executable_schema(type_defs, query)

    app = Flask(__name__)


    @app.route("/graphql", methods=["GET"])
    def graphql_playgroud():
        # On GET request serve GraphQL Playground
        # You don't need to provide Playground if you don't want to
        # but keep on mind this will not prohibit clients from
        # exploring your API using desktop GraphQL Playground app.
        return PLAYGROUND_HTML, 200


    @app.route("/graphql", methods=["POST"])
    def graphql_server():
        # GraphQL queries are always sent as POST
        data = request.get_json()

        # Note: Passing the request to the context is optional.
        # In Flask, the current request is always accessible as flask.request
        success, result = graphql_sync(
            schema,
            data,
            context_value=request,
            debug=app.debug
        )

        status_code = 200 if success else 400
        return jsonify(result), status_code


    if __name__ == "__main__":
        app.run(debug=True)


Starlette integration
---------------------

Ariadne is an ASGI application that can be directly mounted under Starlette. It will support both HTTP and WebSocket traffic used by subscriptions::

    from ariadne import QueryType, make_executable_schema
    from ariadne.asgi import GraphQL
    from starlette.applications import Starlette

    type_defs = """
        type Query {
            hello: String!
        }
    """

    query = QueryType()


    @query.field("hello")
    def resolve_hello(*_):
        return "Hello world!"


    # Create executable schema instance
    schema = make_executable_schema(type_defs, query)

    app = Starlette(debug=True)
    app.mount("/graphql", GraphQL(schema, debug=True))
