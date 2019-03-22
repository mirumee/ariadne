.. _schema-binding:

Binding to schema
=================

When Ariadne initializes GraphQL server, it iterates over a list of objects passed to a ``resolvers`` argument of ``make_executable_schema`` and calls ``bind_to_schema`` method of each item with a single argument: instance of ``GraphQLSchema`` object representing parsed schema used by the server.


Implementing custom types
-------------------------

You can easily implement a custom type that can be used with ``make_executable_schema``. It only needs to define the ``bind_to_schema`` and, if you are using static typing system like ``MyPy``, extend ``SchemaBindable`` type::

    from graphql.type import GraphQLSchema
    from ariadne import SchemaBindable

    class MyCustomType(SchemaBindable):
        def bind_to_schema(self, schema: GraphQLSchema) -> None:
            pass  # insert custom logic here
