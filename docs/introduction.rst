Introduction
============

Welcome to Ariadne!

This guide will introduce you to basic concepts behind creating GraphQL APIs, and show how Ariadne helps you to implement those with little amount of Python code.

At the end of this guide you will have your own simple GraphQL API accessible trough the browser, implementing single field returning "Hello" and user's user agent on query.

Make sure that you've installed Ariadne using ``pip install ariadne``, and that you have your favorite code editor open and ready.


Defining schema
---------------

First, we will with define what data can be obtained from our API. In Ariadne type definitions are Python strings with content written in `Schema Definition Language <https://graphql.github.io/learn/schema/>`_ (the "SDL"), special language for specifying GraphQL schemas.

We will start with defining special type ``Query`` that GraphQL services use as entry point for all reading operations. Next we will specify single field on it, named ``hello``, and define that it will return value of type ``String``, and that it will never return ``null``.

Using the SDL, our ``Query`` type will look like this::

    type_defs = """
        type Query {
            hello: String!
        }
    """

The ``type Query { }`` block declares the type, ``hello:`` is field definition, ``String`` is return value type, and exclamation mark following it means that this value can't be ``null``.


Resolvers
---------

The resolvers are functions mediating between API consumers and application's business logic. Every type has fields, and every field has a resolver function.

We want our API to greet clients with "Hello (user agent)!". This means that ``hello`` field has to have a resolver that somehow finds client's user agent, and returns greeting message from it.

We know that resolver is a function that returns value, so let's begin with that::

    def resolve_hello(*_):
        return "Hello..."  # What's next?


Above code is perfectly valid, minimal resolver meeting the requirements of our schema. It takes any arguments, does nothing with them and returns blank greeting string. The real world resolvers are rarely that simple: usually they read data from some source such as database, or resolve value in context of parent object.

In Ariadne every field resolver is called with at least two arguments: ``parent`` object, and query's execution ``info``, that usually contains the ``context`` attribute that is GraphQL way of passing additional information from application to its query resolvers.

Default GraphQL server implementation provided by Ariadne defines ``info.context`` as Python ``dict`` containing single key ``environ`` containing basic request data. We can use that in our resolver::

    def resolve_hello(_, info):
        request = info.context["environ"]
        user_agent = request.get("HTTP_USER_AGENT", "guest")
        return "Hello, %s!" % user_agent

Notice that we are discarding first argument in our resolver. This is because ``resolve_hello`` is special type of resolver called *root resolver*, and by default those have no parent object that would get passed to them.

Now we need to map our resolver to ``hello`` field of type ``Query``. To do this will create special dictionary where every key is name of type. This key's value in turn will be another dictionary, mapping fields to resolvers::

    resolvers = {
        "Query": {
            "hello": resolve_hello
        }
    }

Dictionary mapping resolvers to schema is called *resolvers map*.


Testing the API
---------------

Now we have everything we need to finish our API, with only piece missing being http server that would receive the HTTP requests, and return responses.

This is where Ariadne comes in to action. One of utilities that Ariadne provides to developers is a WSGI middleware that can also be ran as simple http server for developers to experiment with GraphQL locally.

.. warning::
   Please never run ``GraphQLMiddleware`` in production without proper WSGI container such as uWSGI or Gunicorn.

This middleware can be imported directly from from ``ariadne`` package, so lets add appropriate import at beginning of our script::

    from ariadne import GraphQLMiddleware

We will now call ``GraphQLMiddleware.make_simple_server`` class method with ``type_defs`` and ``resolvers`` as its arguments to construct simple dev server that we can then start::

    print("Visit the http://127.0.0.1:8888 in the browser and say { hello }!")
    my_api_server = GraphQLMiddleware.make_simple_server(type_defs, resolvers)
    my_api_server.serve_forever()

Run your script with ``python myscript.py`` (remember to replace ``myscript.py`` with name of your file!). If all is well, you will see message telling you to visit the http://127.0.0.1:8888 and say ``{ hello }``.

This the GraphQL Playground, open source API explorer for GraphQL APIs. You can enter ``{ hello }`` query on the left, press big bright "run" button, and see the result on the right:

.. image:: _static/hello-world.png
   :alt: Your first Ariadne GraphQL in action!
   :target: _static/hello-world.png

Your first GraphQL API build with Ariadne is now complete. Congratulations!


Completed code
--------------

For reference here is complete code of the API from this guide::

    from ariadne import GraphQLMiddleware

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

    print("Visit the http://127.0.0.1:8888 in the browser and say { hello }!")
    my_api_server = GraphQLMiddleware.make_simple_server(type_defs, resolvers)
    my_api_server.serve_forever()
