.. _schema-bindables:

Bindables
=========

In Ariadne bindables are special types implementing the logic required for *binding* Python callables and values to the GraphQL schema.


Schema validation
-----------------

Standard bindables provided by the library include validation logic that raises ``ValueError`` when bindable's GraphQL type is not defined by the schema, is incorrect or missing a field.


Creating custom bindable
------------------------

While Ariadne already provides bindables for all GraphQL types, you can also create your own bindables. Potential use cases for custom bindables include be adding abstraction or boiler plate for mutations or some of types used in the schema.

Custom bindable should extend the ``SchemaBindable`` base type and define ``bind_to_schema`` method that will receive single argument, instance of ``GraphQLSchema`` from `graphql-core-next <https://github.com/graphql-python/graphql-core-next>` when on executable schema creation::

    from graphql.type import GraphQLSchema
    from ariadne import SchemaBindable

    class MyCustomType(SchemaBindable):
        def bind_to_schema(self, schema: GraphQLSchema) -> None:
            pass  # insert custom logic here
