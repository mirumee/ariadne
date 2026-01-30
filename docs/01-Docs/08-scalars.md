---
id: scalars
title: Custom scalars
---

GraphQL standard describes plenty of default GraphQL scalars: `Int`, `String` or `Boolean` to name a few. But what when those types are not enough for our API?

This is where custom scalars enter the stage, enabling better control on how Python objects and values are represented in GraphQL query inputs and results.


## Basic custom scalar

The minimum work required to add custom scalar to GraphQL server is to declare it in the schema using the `scalar` keyword:

```graphql
scalar Money

type Query {
    revenue: Money
}
```

In the above example we have declared custom scalar named `Money` and used it as an return value for `revenue` field defined on the `Query` type.

What will happen now if we will return any value from our `revenue` resolver and query for it?

```python
def resolve_revenue(*_):
    revenue = get_revenue()
    return {"amount": revenue, "currency": DEFAULT_CURRENCY}
```

```graphql
query {
    revenue
}
```

We will find that our value will be JSON-serialized:

```json
{
    "data": {
        "revenue": {
            "amount": 10.5,
            "currency": "USD"
        }
    }
}
```

This is a default behaviour for custom scalars: their values are JSON-serialized when included in query results.

If resolver returns value that's not JSON serializable, GraphQL server will fail while creating Query result, and will return error 500 to the client, with error similar to one below being logged by the application:

```
TypeError: Object of type date is not JSON serializable
```

If value for our scalar appears in JSON with variables, its JSON representation will parsed. Likewise, if value appears within query, its AST (abstract syntax tree) representation will be automatically converted to matching Python representation:

```graphql
scalar Money

type Query {
    revenue: Money
}

type Mutation {
    postSale(price: Money!, ref: String!): Boolean
}
```

```graphql
mutation PostSale {
    postSale(price: {amount: 9.99, currency: "USD"}, "usd-2412")
}
```

```python
def resolve_post_sale(*_, price, ref):
    repr(price)  # {'amount': 9.99, 'currency': 'USD'}
```

If JSON with variables or Query AST is incorrect the server will return `400 BAD REQUEST` and will not attempt to execute query.


## Customizing scalar serialization

Consider this API defining the `Story` type with the `publishedOn` field thats date of story publication:

```graphql
type Story {
    content: String
    publishedOn: String
}
```

The `publishedOn` field resolver returns an instance of type `datetime`, but in the API this field is defined as `String`. This means that our datetime will be passed through the `str()` function before being returned to the client:

```json
{
    "publishedOn": "2018-10-26 17:28:54.416434"
}
```

This may look acceptable, but there are better formats to serialize timestamps for later deserialization on the client, like ISO 8601. This conversion could be performed in a dedicated resolver:

```python
def resolve_published_on(obj, *_):
    return obj.published_on.isoformat()
```

However, the developer now has to remember to define a custom resolver for every field that returns `datetime`. This really adds boilerplate to the API, and makes it harder to use abstractions auto-generating the resolvers for you.

Instead, GraphQL API can be told how to serialize dates by defining the custom scalar type:

```graphql
scalar Datetime

type Story {
    content: String
    publishedOn: Datetime
}
```

If you try to query this field now, the server will crash with error 500 and following error will be logged:

```
TypeError: Object of type date is not JSON serializable
```

This is because a custom scalar has been defined, but it's currently missing logic for serializing Python values to JSON form and `Datetime` instances are not JSON serializable by default.

We need to tell our GraphQL server how `Datetime` scalar values should be converted in order for them to be JSON serializable.

Ariadne provides the `ScalarType` class that enables us to implement this behaviour using Python function:

```python
from ariadne import ScalarType

datetime_scalar = ScalarType("Datetime")

@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()
```

Now we need to include the `datetime_scalar` on the executable schema creation:

```python
schema = make_executable_schema(type_defs, some_type, some_other_type, datetime_scalar)
```

Custom serialization logic will now be used when a resolver for the `Datetime` field returns a value other than `None`:

```json
{
    "publishedOn": "2018-10-26T17:45:08.805278"
}
```

We can now reuse our custom scalar across the API to serialize `datetime` instances in a standardized format that our clients will understand.


## Scalars as input

What will happen if now we create a field or mutation that defines an argument of the type `Datetime`? We can find out using a basic resolver:

```graphql
type Query {
    stories(publishedOn: Datetime): [Story!]!
}
```

```python
def resolve_stories(*_, **data):
    print(data.get("publishedOn"))  # what value will "publishedOn" be?
```

`data.get("publishedOn")` will print a result of JSON parsing whatever value was passed to the field. It may be a string with ISO 8601 representation of date but it may also be an integer, float, or some complex type like dict or list.

We will need to add custom parsing logic on top of whatever JSON and GraphQL parsers are doing in order for our scalar to be helpful. To do that, we will need to implement another Python function called _"value parser"_ and use `ScalarType` that was created in the previous step to make GraphQL server use it for parsing incoming value:

```python
@datetime_scalar.value_parser
def parse_datetime_value(value):
    # dateutil is provided by python-dateutil library
    return dateutil.parser.parse(value)
```

There are a few things happening in the above code, so let's go through it step by step:

1. If the `value` is passed as part of a query's `variables`, `parse_datetime_value` will be called with it as only argument, but only if its not `null`.
2. `dateutil.parser.parse` is used to parse it to the valid Python `datetime` object instance that is then returned.
3. If `value` is incorrect and either a `ValueError` or `TypeError` exception is raised by the `dateutil.parser.parse`.

If error was raised, the GraphQL server interprets this as a sign that the entered value is incorrect because it can't be transformed to an internal representation and returns an automatically generated error message to the client:

```
Expected type Datetime!, found "invalid string": time data 'invalid string' does not match format '%Y-%m-%d'
```

An error will also be logged:

```
time data 'invalid string' does not match format '%Y-%m-%d'
```

Because the error message returned by the GraphQL server includes the original exception message from your Python code, it may contain details specific to your system or implementation that you may not want to make known to the API consumers. You may decide to catch the original exception with `except (ValueError, TypeError)` and then raise your own `ValueError` with a custom message (or no message at all) to prevent this from happening:

```python
@datetime_scalar.value_parser
def parse_datetime_value(value):
    try:
        return dateutil.parser.parse(value)
    except (ValueError, TypeError):
        raise ValueError(f'"{value}" is not a valid ISO 8601 string')
```

> There is no difference in handling between `ValueError` and `TypeError`. Both will produce the same error message in Query result.


## Configuration reference

In addition to the decorators documented above, `ScalarType` provides two more ways for configuring its logic.

You can pass your functions as values to `serializer`, `value_parser` keyword arguments on instantiation:

```python
from ariadne import ScalarType
from thirdpartylib import json_serialize_money, json_deserialize_money

money = ScalarType("Money", serializer=json_serialize_money, value_parser=json_deserialize_money)
```

Alternatively you can use `set_serializer`, `set_value_parser` setters:

```python
from ariadne import ScalarType
from thirdpartylib import json_serialize_money, json_deserialize_money

money = ScalarType("Money")
money.set_serializer(json_serialize_money)
money.set_value_parser(json_deserialize_money)
```

> **Note:** the previous versions of this document also introduced the `literal_parser`. However in the light of `literal_parser` [reference documentation being incorrect](https://github.com/graphql/graphql-js/issues/2567) and the usefulness of custom literal parsers [being discussed](https://github.com/graphql/graphql-js/issues/2657) we've decided to no longer document it in this article.
>
> GraphQL query executor provides default literal parser for all scalars that converts `AST` to Python value then calls scalar's value parser with it, making implementation of custom literal parsers for scalars unnecessary.
