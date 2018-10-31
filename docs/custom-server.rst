Custom server example
=====================

In addition to simple GraphQL server implementation in form of ``GraphQLMiddleware``, Ariadne provides building blocks for assembling custom GraphQL servers.


Creating executable schema
--------------------------

The key piece of the GraphQL server is an *executable schema* - a schema with resolver functions attached to fields.

Ariadne provides a ``make_executable_schema`` utility function that takes type definitions as a first argument and a resolvers map as the second, and returns an executable instance of ``GraphQLSchema``::

    from ariadne import make_executable_schema

    type_defs = """
        type Query {
            hello: String!
        }
    """


    def resolve_hello(_, info):
        request = info.context["environ"]
        user_agent = request.get("HTTP_USER_AGENT", "guest")
        return "Hello, %s!" % user_agent


    resolvers = {
        "Query": {
            "hello": resolve_hello
        }
    }

    schema = make_executable_schema(type_defs, resolvers)
    
This schema can then be passed to the ``graphql`` query executor together with the query and variables::

    from graphql import graphql

    result = graphql(schema, query, variables={})


Basic GraphQL server with Django
--------------------------------

The following example presents a basic GraphQL server using a Django framework::

    import json

    from ariadne import make_executable_schema
    from ariadne.constants import PLAYGROUND_HTML
    from django.http import (
        HttpResponse, HttpResponseBadRequest, JsonResponse
    )
    from django.views import View
    from graphql import format_error, graphql

    type_defs = """
        type Query {
            hello: String!
        }
    """


    def resolve_hello(_, info):
        request = info.context["environ"]
        user_agent = request.get("HTTP_USER_AGENT", "guest")
        return "Hello, %s!" % user_agent


    resolvers = {
        "Query": {
            "hello": resolve_hello
        }
    }

    # Create executable schema instance
    schema = make_executable_schema(type_defs, resolvers)


    # Create GraphQL view
    class GraphQLView(View):
        # On GET request serve GraphQL Playground
        # You don't need to provide Playground if you don't want to
        # bet keep on mind this will nor prohibit clients from
        # exploring your API using desktop GraphQL Playground app.
        def get(self, request, *args, **kwargs):
            return HttpResponse(PLAYGROUND_HTML)

        # GraphQL queries are always sent as POSTd
        def post(self, request, *args, **kwargs):
            # Reject requests that aren't JSON
            if request.content_type != "application/json":
                return HttpResponseBadRequest()

            # Naively read data from JSON request
            try:
                data = json.loads(request.data)
            except ValueError:
                return HttpResponseBadRequest()

            # Check if instance data is not empty and dict
            if not data or not isinstance(data, dict):
                return HttpResponseBadRequest()

            # Check if variables are dict:
            variables = data.get("variables")
            if variables and not isinstance(variables, dict):
                return HttpResponseBadRequest()

            # Execute the query
            result = graphql(
                schema,
                data.get("query"),
                context=request,  # expose request as info.context
                variables=data.get("variables"),
                operation_name=data.get("operationName"),
            )

            # Build valid GraphQL API response
            status = 200
            response = {}
            if result.errors:
                response["errors"] = map(format_error, result.errors)
            if result.invalid:
                status = 400
            else:
                response["data"] = result.data

            # Send response to client
            return JsonResponse(response, status=status)