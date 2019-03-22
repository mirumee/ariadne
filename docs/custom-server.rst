Custom server example
=====================

In addition to simple a GraphQL server implementation in the form of ``GraphQLMiddleware``, Ariadne provides building blocks for assembling custom GraphQL servers.


Creating executable schema
--------------------------

The key piece of the GraphQL server is an *executable schema* - a schema with resolver functions attached to fields.

Ariadne provides a ``make_executable_schema`` utility function that takes type definitions as a first argument and a resolvers map as the second, and returns an executable instance of ``GraphQLSchema``::

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

    from ariadne import QueryType, make_executable_schema
    from ariadne.constants import PLAYGROUND_HTML
    from django.http import (
        HttpResponse, HttpResponseBadRequest, JsonResponse
    )
    from django.views import View
    from graphql import format_error, graphql_sync

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


    # Create GraphQL view
    class GraphQLView(View):
        # On GET request serve GraphQL Playground
        # You don't need to provide Playground if you don't want to
        # but keep on mind this will not prohibit clients from
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
                data = json.loads(request.body)
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
            result = graphql_sync(
                schema,
                data.get("query"),
                context_value=request,  # expose request as info.context
                variable_values=data.get("variables"),
                operation_name=data.get("operationName"),
            )

            # Build valid GraphQL API response
            response = {"data": result.data}
            if result.errors:
                response["errors"] = [format_error(e) for e in result.errors]

            # Send response to client
            return JsonResponse(response)
