---
id: resolvers
title: Resolvers
---


In Ariadne, a resolver is any Python callable both asynchronous and synchronous that accepts two positional arguments (`obj` and `info`):

```python
def example_resolver(obj: Any, info: GraphQLResolveInfo):
    return obj.do_something()

class FormResolver:
    def __call__(self, obj: Any, info: GraphQLResolveInfo, **data):
        ...
```

`obj` is a value returned by a parent resolver. If the resolver is a *root resolver* (it belongs to the field defined on `Query`, `Mutation` or `Subscription`) and the GraphQL server implementation doesn't explicitly define value for this field, the value of this argument will be `None`.

`info` is the instance of a `GraphQLResolveInfo` object specific for this field and query. It defines a special `context` attribute that contains any value that GraphQL server provided for resolvers on the query execution. Its type and contents are application-specific, but it is generally expected to contain application-specific data such as authentication state of the user or an HTTP request.

> `context` is just one of many attributes that can be found on `GraphQLResolveInfo`, but it is by far the most commonly used one. Other attributes enable developers to introspect the query that is currently executed and implement new utilities and abstractions, but documenting that is out of Ariadne's scope. If you are interested, you can find the list of all attributes [here](https://github.com/graphql-python/graphql-core/blob/v3.0.3/src/graphql/type/definition.py#L533).


## Binding resolvers

A resolver needs to be bound to a valid type's field in the schema in order to be used during the query execution.

To bind resolvers to schema, Ariadne uses a special `ObjectType` class that is initialized with a single argument: the name of the type defined in the schema:

```python
from ariadne import ObjectType

query = ObjectType("Query")
```

The above `ObjectType` instance knows that it maps its resolvers to `Query` type, and enables you to assign resolver functions to these type fields. This can be done using the `field` decorator implemented by the resolver map:

```python
from ariadne import ObjectType, make_executable_schema

type_defs = """
    type Query {
        hello: String!
    }
"""

query = ObjectType("Query")

@query.field("hello")
def resolve_hello(*_):
    return "Hello!"


schema = make_executable_schema(type_defs, query)
```

If you need to add resolvers for another type, you can pass it as another argument to the executable schema:

```python
from ariadne import ObjectType, make_executable_schema

type_defs = """
    type Query {
        hello: String!
        user: User
    }

    type User {
        username: String!
    }
"""

query = ObjectType("Query")


@query.field("user")
def resolve_user(_, info):
    return {"first_name": "John", "last_name": "Lennon"}


user = ObjectType("User")

@user.field("username")
def resolve_username(obj, *_):
    return f"{obj['first_name']} {obj['last_name']}"


schema = make_executable_schema(type_defs, query, user)
```

> **Note**
>
> In previous versions of Ariadne recommended approach to passing multiple bindables to `make_executable_schema` was to combine those into a list:
>
> ```python
> schema = make_executable_schema(type_defs, [query, user])
> ```
>
> This pattern is still supported for backwards compatibility reasons, but it may be deprecated in future version of Ariadne.

In the above example we define resolvers for two GraphQL types: `Query` and `User`. GraphQL knows that those two are connected thanks to relationships in schema. Take this query for example:

```graphql
{
    user {
        username
    }
}
```

When the GraphQL server receives this query, it will first call the `resolve_user` function assigned to the `user` field on the `Query` type. If this function returns value, the GraphQL server will next look up the type that this value represents. It knows from the schema that the `user` field resolves to the `User` type. So GraphQL will look up resolvers for the `User` fields and will call the `resolve_username` function of the `User` type with value returned from the `resolve_user` function as first argument.

The `@query.field` decorator is non-wrapping - it simply registers a given function as a resolver for the specified field and then returns it as it is. This makes it easy to test or reuse resolver functions between different types or even APIs:

```python
user = ObjectType("User")
client = ObjectType("Client")

@user.field("email")
@client.field("email")
def resolve_email_with_permission_check(obj, info):
    if info.context["user"].is_administrator:
        return obj.email
    return None
```

Alternatively, `set_field` method can be used to set function as field's resolver:

```python
from .resolvers import resolve_email_with_permission_check

user = ObjectType("User")
user.set_field("email", resolve_email_with_permission_check)
```


## Handling arguments

If a GraphQL field specifies any arguments, those argument values will be passed to the resolver as keyword arguments:

```python
type_def = """
    type Query {
        holidays(year: Int): [String]!
    }
"""

query = ObjectType("Query")

@query.field("holidays")
def resolve_holidays(*_, year=None):
    if year:
        return Calendar.get_holidays_in_year(year)
    return Calendar.get_all_holidays()
```

If a field argument is marked as required (by following its type with `!`, eg. `year: Int!`), you can skip the `=None` in your `kwarg`:

```python
@query.field("holidays")
def resolve_holidays(*_, year):
    if year:
        return Calendar.get_holidays_in_year(year)
    return Calendar.get_all_holidays()
```

> **Note:** You can decorate your resolvers with [`convert_kwargs_to_snake_case`](../API-reference/api-reference#convert_kwargs_to_snake_case) to convert arguments and inputs names from `camelCase` to `snake_case`.
>
> **Deprecated:** `convert_kwargs_to_snake_case` decorator is a legacy feature that will be deprecated in future Ariadne release. See the "[Names case conversion](case-conversion)" chapter for new solution.


## Aliases

You can use `ObjectType.set_alias` to quickly make a field an alias for a differently-named attribute on a resolved object:

```python
type_def = """
    type User {
        fullName: String
    }
"""

user = ObjectType("User")
user.set_alias("fullName", "username")
```


## Fallback resolvers

> **Deprecated:** Fallback resolvers are legacy feature that will be deprecated in future Ariadne release. See the "[Names case conversion](case-conversion)" chapter for new solution.

Schema can potentially define numerous types and fields, and defining a resolver or alias for every single one of them can become a large burden.

Ariadne provides two special "fallback resolvers" that scan schema during initialization, and bind default resolvers to fields that don't have any resolver set:

```python
from ariadne import fallback_resolvers, make_executable_schema
from .typedefs import type_defs
from .resolvers import resolvers

schema = make_executable_schema(type_defs, resolvers, fallback_resolvers)
```

The above example creates an executable schema using types and resolvers imported from other modules, but it also adds `fallback_resolvers` to the list of bindables that should be used in creation of the schema.

Resolvers set by `fallback_resolvers` don't perform any case conversion and simply seek the attribute named in the same way as the field they are bound to using the "default resolver" strategy described in the next chapter.

If your schema uses JavaScript convention for naming its fields (as do all schema definitions in this guide) you may want to instead use the `snake_case_fallback_resolvers` that converts field name to Python's `snake_case` before looking it up on the object:

```python
from ariadne import snake_case_fallback_resolvers, make_executable_schema
from .typedefs import type_defs
from .resolvers import resolvers

schema = make_executable_schema(type_defs, resolvers, snake_case_fallback_resolvers)
```


## Default resolver

Both `ObjectType.alias` and fallback resolvers use a default resolver provided by `graphql-core` library to implement its functionality.

This resolver takes a target attribute name and (depending if `obj` is a `dict` or not) uses either `obj.get(attr_name)` or `getattr(obj, attr_name, None)` to resolve the value that should be returned. If the resolved value is a callable, it is then called with the `GraphQLResolveInfo` instance as only positional argument with field's arguments being passed as named arguments, and its return value is then used instead.

In the below example, both representations of `User` type are supported by the default resolver:

```python
type_def = """
    type User {
        username: String!
        likes: Int!
        initials(length: Int!): String
    }
"""

class UserObj:
    username = "admin"

    def likes(self, info):
        return count_user_likes(self)

    def initials(self, info, *, length):
        return self.username[:length]

user_dict = {
    "username": "admin",
    "likes": lambda info: count_user_likes(obj),
    "initials": lambda info, *, length: obj.username[:length]
}
```


## Query shortcut

Ariadne defines the `QueryType` shortcut that you can use in place of `ObjectType("Query")`:

```python
from ariadne import QueryType

type_def = """
    type Query {
        systemStatus: Boolean!
    }
"""

query = QueryType()

@query.field("systemStatus")
def resolve_system_status(*_):
    ...
```
