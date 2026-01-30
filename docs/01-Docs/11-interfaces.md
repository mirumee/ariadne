---
id: interfaces
title: Interface types
---


An `interface` is an abstract GraphQL type that defines a certain set of fields.  Any other type that contains the same set of fields is said to *implement* that `interface`. Types that implement an `interface` are not limited by it. In other words, a type can implement an `interface`'s fields as well as additional fields.  The key point is that a type must implement **at least** the fields of an `interface` in order for the schema to be correct.  

## Interface example

Consider an application implementing a search function. Search can return items of different types, like `Client`, `Order` or `Product`. For each result it displays a short summary text that is a link leading to a page containing the item's details.

An `Interface` can be defined in the schema that forces those types to define the `summary` and `url` fields:

```graphql
interface SearchResult {
    summary: String!
    url: String!
}
```

Type definitions can then be updated to `implement` this interface:

```graphql
type Client implements SearchResult {
    first_name: String!
    last_name: String!
    summary: String!
    url: String!
}

type Order implements SearchResult {
    ref: String!
    client: Client!
    summary: String!
    url: String!
}

type Product implements SearchResult {
    name: String!
    sku: String!
    summary: String!
    url: String!
}
```

The GraphQL standard requires that every type implementing the `Interface` also explicitly defines fields from the interface. This is why the `summary` and `url` fields repeat on all types in the example.

Like with the `Union`, the `SearchResult` interface will also need a special resolver called a *type resolver*. This resolver will be called with an object returned from a field resolver and the current context. It should return a string containing the name of a GraphQL type, or `None` if the received type is incorrect:

```python
def resolve_search_result_type(obj, *_):
    if isinstance(obj, Client):
        return "Client"
    if isinstance(obj, Order):
        return "Order"
    if isinstance(obj, Product):
        return "Product"
    return None
```

> Returning `None` from this resolver will result in `null` being returned for this field in your query's result. If a field is not nullable, this will cause the GraphQL query to error.

Ariadne relies on a dedicated `InterfaceType` class for binding this function to the `Interface` in your schema:

```python
from ariadne import InterfaceType

search_result = InterfaceType("SearchResult")

@search_result.type_resolver
def resolve_search_result_type(obj, *_):
    ...
```

If this function is already defined elsewhere (e.g. 3rd party package), you can instantiate the `InterfaceType` with it as a second argument:

```python
from ariadne import InterfaceType
from .graphql import resolve_search_result_type

search_result = InterfaceType("SearchResult", resolve_search_result_type)
```

Lastly, your `InterfaceType` instance should be passed to `make_executable_schema` together with your other types:

```python
schema = make_executable_schema(type_defs, [query, search_result])
```


## Field resolvers

Ariadne's `InterfaceType` instances can optionally be used to set resolvers on implementing types' fields.

The `SearchResult` interface from the previous section implements two fields: `summary` and `url`. If the resolver implementation for those fields is same for multiple types implementing the interface, the `InterfaceType` instance can be used to set those resolvers for those fields:

```python
@search_result.field("summary")
def resolve_summary(obj, *_):
    return str(obj)


@search_result.field("url")
def resolve_url(obj, *_):
    return obj.get_absolute_url()
```

`InterfaceType` extends the [ObjectType](resolvers) class, so `set_field` and `set_alias` are also available:

```python
search_result.set_field("summary", resolve_summary)
search_result.alias("url", "absolute_url")
```

> `InterfaceType` assigns the resolver to a field only if that field doesn't already have a resolver set. This is different from an `ObjectType` that can set a resolver to a field even if the field already has another resolver set.
