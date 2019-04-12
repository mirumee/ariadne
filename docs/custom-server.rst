Integrations
============

Ariadne provides helper functions for the three common operations.

.. cofunction:: ariadne.graphql(schema, data, [root_value=None, context_value=None, debug=False, validation_rules, error_formatter, middleware], **kwargs)

    :param schema: an executable schema created using `make_executable_schema`
    :param data: decoded input data sent by the client (eg. for POST requests in JSON format, pass in the structure decoded from JSON), exact shape of `data` will depend on the query type and protocol
    :param root_value: the value passed to the root-level resolvers
    :param context_value: the context value passed to all resolvers (it's common for your context to include the request object specific to your web framework)
    :param debug: if `True` will cause the server to include debug information in error responses
    :param validation_rules: optional additional validators (as defined by `graphql.validation.rules`) to run before attempting to execute the query (the standard validators defined by the GraphQL specification are always used and there's no need to provide them here)
    :param error_formatter: an optional custom function to use for formatting errors, the function will be passed two parameters: a `GraphQLError` exception instance, and the value of the `debug` switch
    :param middleware: optional middleware to wrap the resolvers with
    :return: `(success, response)`, a tuple of two values, the success indicator (boolean), and the response to send to the client (will need to be encoded into an appropriate format)

    This function is an asynchronous coroutine so you will need to ``await`` on the returned value.

    .. warning::

        Coroutines will not work under WSGI. If your server uses WSGI (Django and Flask do), see below for a synchronous alternative.


.. function:: ariadne.graphql_sync(schema, data, [root_value=None, context_value=None, debug=False, validation_rules, error_formatter, middleware], **kwargs)

    Parameters are the same as those of the ``graphql`` coroutine above but the function is blocking and the result is returned synchronously.


.. cofunction:: ariadne.subscribe(schema, data, [root_value=None, context_value=None, debug=False, validation_rules, error_formatter], **kwargs)

    Parameters are the same as those of the ``graphql`` coroutine except for the ``middleware`` parameter that is not supported.

    This function is an asynchronous coroutine so you will need to ``await`` on the returned value.


Django Integrating
------------------

The following example presents a GraphQL server running as a Django view::

    import json

    from ariadne import QueryType, graphql_sync, make_executable_schema
    from ariadne.constants import PLAYGROUND_HTML
    from django.conf import settings
    from django.http import (
        HttpResponseBadRequest, JsonResponse
    )
    from django.views.decorators.csrf import csrf_exempt

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


    # Create the view
    @csrf_exempt
    def graphql_view(request):
        # On GET request serve GraphQL Playground
        # You don't need to provide Playground if you don't want to
        # but keep on mind this will not prohibit clients from
        # exploring your API using desktop GraphQL Playground app.
        if request.method == "GET":
            return HttpResponse(PLAYGROUND_HTML)

        # GraphQL queries are always sent as POST
        if request.method != "POST":
            return HttpResponseBadRequest()

        if request.content_type != "application/json":
            return HttpResponseBadRequest()

        # Naively read data from JSON request
        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest()

        # Execute the query
        success, result = graphql_sync(
            schema,
            data,
            context_value=request,  # expose request as info.context
            debug=settings.DEBUG,
        )

        status_code = 200 if success else 400
        # Send response to client
        return JsonResponse(result, status=status_code)
