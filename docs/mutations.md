---
id: mutations
title: Mutations
---


All the previous examples in this documentation have dealt with the `Query` root type and reading data. What about creating, updating or deleting data?

Enter the `Mutation` type, `Query`'s sibling that GraphQL servers use to implement functions that change application state.

> Because there is no restriction on what can be done inside resolvers, technically there's nothing stopping somebody from making `Query` fields act as `Mutation`s, taking inputs and executing state-changing logic.
>
> In practice, such queries break the contract with client libraries such as Apollo-Client that do client-side caching and state management, resulting in non-responsive controls or inaccurate information being displayed in the UI as the library displays cached data before redrawing it to display an actual response from the GraphQL.


## Defining mutations

Let's define the basic schema that implements a simple authentication mechanism allowing the client to see if they are authenticated, and to log in and log out:

```python
type_def = """
    type Query {
        isAuthenticated: Boolean!
    }

    type Mutation {
        login(username: String!, password: String!): Boolean!
        logout: Boolean!
    }
"""
```

In this example we have the following elements:

- `Query` type with single field: a boolean for checking if we are authenticated or not. It may appear superficial for the sake of this example, *but Ariadne requires* that your GraphQL API always defines a `Query` type.
- `Mutation` type with two mutations:
    - `login` mutation that requires username and password strings and returns a boolean indicating status.
    - `logout` that takes no arguments and just returns status.


## Writing resolvers

Mutation resolvers are no different than resolvers used by other types. They are functions that take `parent` and `info` arguments, as well as any mutation's arguments as keyword arguments. They then return data that should be sent to the client as a query result:

```python
def resolve_login(_, info, username, password):
    request = info.context["request"]
    user = auth.authenticate(username, password)
    if user:
        auth.login(request, user)
        return True
    return False


def resolve_logout(_, info):
    request = info.context["request"]
    if request.user.is_authenticated:
        auth.logout(request)
        return True
    return False
```

You can map resolvers to mutations using a `MutationType` object:

```python
from ariadne import MutationType
from . import auth_mutations

mutation = MutationType()
mutation.set_field("login", auth_mutations.resolve_login)
mutation.set_field("logout", auth_mutations.resolve_logout)
```

> `MutationType()` is just a shortcut for `ObjectType("Mutation")`.

`MutationType` objects include a `field()` decorator for mapping resolvers to mutations:

```python
mutation = MutationType()

@mutation.field("logout")
def resolve_logout(_, info):
    ...
```

> **Binding Mutation Resolvers**
>
> Recall that resolvers need to be bound to their respective resolvers via the `make_executable_schema` call. If you're following along from the introduction that call will look similar to the following:
>
> ```python
> make_executable_schema(type_defs, [query, mutations])
> ```

## Mutation results

The `login` and `logout` mutations introduced earlier in this guide work, but give very limited feedback to the client: they return either `False` or `True`.  The application could use additional information like an error message that could be displayed in the interface if the mutation request fails, or a user state updated after a mutation completed.

In GraphQL this is achieved by making mutations return special *result* types containing additional information about the result, such as errors or current object state:

```python
type_def = """
    type Mutation {
        login(username: String!, password: String!): LoginResult
    }

    type LoginResult {
        status: Boolean!
        error: Error
        user: User
    }
"""
```

The above mutation will return a special type containing information about the mutation's status, as well as either an `Error` message or a logged in `User`. In Python this result can be represented as a simple `dict`:

```python
def resolve_login(_, info, username, password):
    request = info.context["request"]
    user = auth.authenticate(username, password)
    if user:
        auth.login(request, user)
        return {"status": True, "user": user}
    return {"status": False, "error": "Invalid username or password"}
```

Let's take one more look at the result's fields:

- `status` makes it easier for the frontend logic to check if mutation succeeded or not.
- `error` contains an error message returned by mutation or `null`. Errors can be simple strings, or more complex types that contain additional information for use by the client.

`user` field is especially noteworthy. Modern GraphQL client libraries like [Apollo Client](https://www.apollographql.com/docs/react/) implement automatic caching and state management, using GraphQL types to track and automatically update stored object data whenever a new one is returned from the API.

Consider a mutation that changes a user's username and its result:

```graphql
type Mutation {
    updateUsername(id: ID!, username: String!): userMutationResult
}

type UsernameMutationResult {
    status: Boolean!
    error: Error
    user: User
}
```

Our client code may first perform an *optimistic update* before the API executes a mutation and returns a response to client. This optimistic update will cause an immediate update of the application interface, making it appear fast and responsive to the user. When the mutation eventually completes a moment later and returns an updated `user` one of two things will happen:

If the mutation succeeded, the user doesn't see another UI update because the new data returned by the mutation was the same as the one set by the optimistic update. If the mutation asked for additional user fields that are dependant on username but weren't set optimistically (like link or user name changes history), those will be updated too.

If the mutation failed, changes performed by an optimistic update are overwritten by valid user state that contains the pre-changed username. The client then uses the `error` field to display an error message in the interface.

For the above reasons it is considered a good design for mutations to return an updated object whenever possible.

> There is no requirement for every mutation to have its own `Result` type. `login` and `logout` mutations can both define `LoginResult` as their return type. It is up to the developer to decide how generic or specific mutation results should be.
