---
id: bindables
title: Bindables
---


In Ariadne bindables are special types implementing the logic required for *binding* Python callables and values to the GraphQL schema.


## Schema validation

Standard bindables provided by the library include validation logic that raises `ValueError` when a bindable's GraphQL type is not defined by the schema, is incorrect, or missing a field.


## Creating custom bindable

While Ariadne already provides bindables for all GraphQL types, you can also create your own bindables. Potential use cases for custom bindables include adding an abstraction, or boilerplate for mutations or some types used in the schema.

Custom bindables should extend the [`SchemaBindable`](../API-reference/types-reference#schemabindable) base type and define the `bind_to_schema` method that will receive a single argument, an instance of `GraphQLSchema` (from [graphql-core](https://github.com/graphql-python/graphql-core)):

```python
from graphql.type import GraphQLSchema
from ariadne import SchemaBindable

class MyCustomType(SchemaBindable):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        pass  # insert custom logic here
```

`bind_to_schema` is called during executable schema creation.
