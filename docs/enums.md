---
id: enums
title: Enumeration types
---


Ariadne supports GraphQL [enumeration types](https://graphql.org/learn/schema/#enumeration-types) which by default are represented as strings in Python logic:

```python
from ariadne import QueryType
from db import get_users

type_defs = """
    type Query{
        users(status: UserStatus): [User]!
    }

    enum UserStatus{
        ACTIVE
        INACTIVE
        BANNED
    }
"""

query = QueryType()

@query.field("users")
def resolve_users(*_, status):
    # Value of UserStatus passed to resolver is represented as Python string
    if status == "ACTIVE":
        return get_users(is_active=True)
    if status == "INACTIVE":
        return get_users(is_active=False)
    if status == "BANNED":
        return get_users(is_banned=True)
```

The above example defines a resolver that returns a list of users based on user status, defined using the `UserStatus` enumerable from the schema.

There is no need for resolver to validate if `status` value belongs to the enum. This is done by GraphQL during query execution. Below query will produce an error:

```graphql
{
    users(status: TEST)
}
```

GraphQL failed to find `TEST` in `UserStatus`, and returned an error without calling `resolve_users`:

```json
{
    "error": {
        "errors": [
            {
                "message": "Argument \"status\" has invalid value TEST.\nExpected type \"UserStatus\", found TEST.",
                "locations": [
                    {
                        "line": 2,
                        "column": 14
                    }
                ]
            }
        ]
    }
}
```


## Associating GraphQL and Python enums

By default enum values are represented as Python strings, but Ariadne also supports associating GraphQL enums with their Python counterparts.

Imagine posts on a social site that can have weights like "standard", "pinned" and "promoted":

```graphql
type Post {
    weight: PostWeight
}

enum PostWeight {
    STANDARD
    PINNED
    PROMOTED
}
```

In the database, the application may store those weights as integers from 0 to 2. You can implement a custom resolver logic transforming GraphQL representation to the integer but you would have to remember to use this boilerplate in every resolver.

Instead, you can define Python version of this enum, and pass it directly to the `make_executable_schema`:

```python
import enum

from ariadne import QueryType, gql, make_executable_schema

type_defs = gql(
    """
    type Query = {
        post: Post!
    }

    type Post {
        weight: PostWeight
    }

    enum PostWeight {
        STANDARD
        PINNED
        PROMOTED
    }
    """
)


# Python enum sharing name with GraphQL enum
class PostWeight(enum.IntEnum):
    STANDARD = 0
    PINNED = 1
    PROMOTED = 2


# Simple query type that returns post with only weight field
query_type = QueryType()

@query_type.field("post")
def resolve_post(*_):
    return {"weight": PostWeight.PINNED}


schema = make_executable_schema(type_defs, query_type, PostWeight)
```

This will make the GraphQL server automatically translate `PostWeight` between their GraphQL and Python values:

- If `PostWeight` enum's value is passed in argument to the GraphQL field, Python resolver will be called with `PostWeight` member, like `PostWeight.PINNED`.
- If Python resolver for field returning GraphQL enum returns Enum member this value will be converted into GraphQL enum. Eg. returning `PostWeight.PROMOTED` from resolver will appear as `"PROMOTED"` in GraphQL result).
- If Python resolver for field returning GraphQL enum returns a value that's valid value of enum's member, this value will be converted into enum. Eg. returning `1` from resolver will appear as `"PINNED"` in GraphQL result).

In this example we've used `IntEnum`, but custom enum can be any subtype of `Enum` type.


## Mapping Python enums by custom name

In above example we've used Python enum `PostWeight` to set Python values for GraphQL enum named `PostWeight`. This worked because Ariadne tries to associate Python objects with their schema counterparts by their name.

But what if enums names differ between GraphQL schema and Python? This is where `EnumType` utility from ariadne becomes useful:

```python
import enum

from ariadne import EnumType, QueryType, gql, make_executable_schema

type_defs = gql(
    """
    type Query = {
        post: Post!
    }

    type Post {
        weight: PostWeightEnum
    }

    enum PostWeightEnum {
        STANDARD
        PINNED
        PROMOTED
    }
    """
)


# Python enum sharing name with GraphQL enum
class PostWeight(enum.IntEnum):
    STANDARD = 0
    PINNED = 1
    PROMOTED = 2


# Simple query type that returns post with only weight field
query_type = QueryType()

@query_type.field("post")
def resolve_post(*_):
    return {"weight": PostWeight.PINNED}


schema = make_executable_schema(
    type_defs,
    query_type,
    # Wrap Python enum in EnumType to give it explicit name in GraphQL schema
    EnumType("PostWeightEnum", PostWeight),
)
```

Ariadne will now know that `PostWeightEnum` in GraphQL schema and `PostWeight` enum in Python are the same type.


## Mapping GraphQL enums to dicts

If `Enum` type is not available for your GraphQL enum, you can pass `dict` to `EnumType`'s second argument:

```python
from ariadne import EnumType

post_weight = EnumType(
    "PostWeight",
    {
        "STANDARD": 0,
        "PINNED": 1,
        "PROMOTED": 2,
    },
)
```


```python
import enum

from ariadne import EnumType, QueryType, gql, make_executable_schema

type_defs = gql(
    """
    type Query = {
        post: Post!
    }

    type Post {
        weight: PostWeightEnum
    }

    enum PostWeightEnum {
        STANDARD
        PINNED
        PROMOTED
    }
    """
)


# Python dict with Python values for GraphQL members
post_weights = {
    "STANDARD": 0,
    "PINNED": 1,
    "PROMOTED": 2,
}


# Simple query type that returns post with only weight field
query_type = QueryType()

@query_type.field("post")
def resolve_post(*_):
    return {"weight": 2}  # 2 will be returned as PROMOTED by GraphQL


schema = make_executable_schema(
    type_defs,
    query_type,
    # Wrap Python dict in EnumType to assignt its values to GraphQL dict
    EnumType("PostWeightEnum", post_weights),
)
```

Conversion logic is mostly same as in case of Python enums:

- If `PostWeightEnum` value is passed in argument to the GraphQL field, Python resolver will be called with corresponding value from `post_weights` dictionary, like `2`.
- If Python resolver for field returning GraphQL enum returns integer that is valid value in `post_weights`, it will be converted into GraphQL enum. Eg. returning `1` from resolver will appear as `"PINNED"` in GraphQL result).
