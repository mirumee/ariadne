Custom server example
=====================

In addition to simple a GraphQL server implementation in the form of ``GraphQLMiddleware``, Ariadne provides building blocks for assembling custom GraphQL servers.


Creating executable schema
--------------------------

The key piece of the GraphQL server is an *executable schema* - a schema with resolver functions attached to fields.

Ariadne provides a ``make_executable_schema`` utility function that takes type definitions as a first argument and bindables as the second, and returns an executable instance of ``GraphQLSchema``::

    from ariadne import QueryType, make_executable_schema

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
    
This schema can then be passed to the ``graphql`` query executor together with the query and variables::

    from graphql import graphql

    result = graphql(schema, query, variable_values={})


Basic GraphQL server with Django
--------------------------------

The following example presents a basic GraphQL server using a Django framework::

    import json

    from ariadne import QueryType, graphql_sync, make_executable_schema
    from ariadne.constants import PLAYGROUND_HTML
    from django.conf import settings
    from django.http import (
        HttpResponseBadRequest, JsonResponse
    )
    from django.views.decorators.csrf import csrf_exempt
    from graphql import graphql_sync

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


Basic GraphQL server with Flask
--------------------------------

The following example presents a basic GraphQL server using a Flask::

    from flask import Flask, request, jsonify
    from ariadne import QueryType, graphql_sync, make_executable_schema
    from ariadne.constants import PLAYGROUND_HTML


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


    app = Flask(__name__)
    schema = make_executable_schema(type_defs, query)


    @app.route('/graphql', methods=['GET'])
    def graphql_playgroud():
        """Serving the GraphQL Playground

        Note: This endpoint is not required if you do not want to provide the playground
        But keep in mind that clients can still explore your API, for example by
        using the GraphQL desktop app.
        """
        return PLAYGROUND_HTML, 200


    @app.route('/graphql', methods=['POST'])
    def graphql_server():
        """Serve GraphQL queries"""
        data = request.get_json()

        # Note: Passing the request to the context is option. In Flask, the current
        #   request is allways accessible as flask.request.
        success, result = graphql_sync(
            schema,
            data,
            context_value=request,
            debug=app.debug
        )

        status_code = 200 if success else 400
        return jsonify(result), status_code


    if __name__ == '__main__':
        app.run(debug=True)
