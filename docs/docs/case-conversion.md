---
id: case-conversion
title: Name case conversion
---

Most common convention for naming fields and arguments in GraphQL is the camel case, where "user birth date" is represented as `userBirthDate`. This is different from Python where object attributes, function names and arguments use the snake case and same "user birth date" becomes `user_birth_date`.

This difference introduces friction to schema-first GraphQL APIs implemented by Python, but there are ways to establish automatic conversion between the two conversions at near-zero performance cost.


## Setting automatic name case conversion for whole schema

`make_executable_schema` function can enable conversion of names case for entire schema when its created.

To do this, add `convert_names_case=True` to its arguments:

```python
schema = make_executable_schema(
    type_defs,
    my_type, my_other_type,
    convert_names_case=True,
)
```

Doing so will result in following changes being made to the GraphQL schema:

- Types fields without resolver already set on them will be assigned a special resolver that seeks Python counterpart of camel case name in object's attributes or dicts keys. Eg. `streetAddress2` field fill be resolved to `street_address_2` attribute for objects and key for dicts.
- Fields arguments without `out_name` already set will be new names
- Inputs fields without `out_name` already set will be set new names


### Custom function for names conversion

If you are not happy with default names conversion method used, you can set `convert_names_case` to a function that should be used to convert the name instead.

This function will be called with three arguments:

- `graphql_name`: a `str` with name to convert.
- `schema`: a `GraphQLSchema` instance for which name conversion is done.
- `path`: a `Tuple[str, ...]` with a path to the schema item for which the name is converted (GraphQL type, field, argument).

It should return a string with a Python name.

Example naive function that converts the name to snake case:

```python
from typing import Tuple

from graphql import GraphQLSchema


def custom_convert_schema_name(
    graphql_name: str, schema: GraphQLSchema, path: Tuple[str, ...]
) -> str:
    converted_name = ""
    for i, c in enumerate(graphql_name.lower()):
        if i == 0:
            converted_name += c
            continue

        if c != graphql_name[i]:
            converted_name += "_"

        converted_name += c
    
    return converted_name


schema = make_executable_schema(
    type_defs,
    my_type, my_other_type,
    convert_names_case=custom_convert_schema_name,
)
```


## Explicit name conversion

If you prefer the _explicit is better than implicit_ approach, here's how to set those names manually:

> **Note:** Mutating `resolve` and `out_name` attributes is considered safe to do if their original value was `None` and the GraphQL server has not started yet. Ariadne limits all mutations of Schema it performs to the `make_executable_schema`, where its not yet available to rest of the application.


### Types fields

Set Python names for types fields, use `set_alias` method of `ObjectType`:

```python
from ariadne import ObjectType, gql, make_executable_schema

type_defs = gql(
    """
    type User {
        lastAction: Int
    }
    """
)

user_type = ObjectType("User")

user_type.set_alias("lastAction", "last_action")

schema = make_executable_schema(type_defs, user_type)
```

Alternatively you can mutate the schema:

```python
from ariadne import gql, make_executable_schema, resolve_to

schema = make_executable_schema(
    gql(
        """
        type Query {
            lastUpdated: Int
        }
        """
    )
)

schema.type_map["Query"].fields["lastUpdated"].resolve = resolve_to("last_updated")
```


### Fields arguments

Set Python names on arguments by mutating their `out_name` attribute:

```python
from ariadne import gql, make_executable_schema

schema = make_executable_schema(
    gql(
        """
        type Query {
            users(orderBy: str): [User!]!
        }

        type User {
            id: ID!
        }
        """
    )
)

schema.type_map["Query"].fields["users"].args["orderBy"].out_name = "order_by"
```


### Inputs fields

Set Python names on input fields by mutating their `out_name` attribute:

```python
from ariadne import gql, make_executable_schema

schema = make_executable_schema(
    gql(
        """
        type Query {
            users(filters: UserFilters): [User!]!
        }

        input UserFilters {
            userName: String
        }

        type User {
            id: ID!
        }
        """
    )
)

schema.type_map["UserFilters"].fields["userName"].out_name = "user_name"
```
