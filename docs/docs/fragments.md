---
id: fragments
title: Fragments
---

GraphQL fragments can be used to give GraphQL queries a structure or extract repeating query sections into reusable parts.

Fragments can be defined **only** in query payload, using the given syntax:

```graphql
fragment fragmentName on TypeName {
    field
    otherField
}
```

`fragmentName` is the fragment's name (any valid GraphQL field name) and `TypeName` is the name of the GraphQL type from the schema for which this fragment is used.

To use fragment in a query, place three dots followed by its name (`...fragmentName`) in a place where its fields should be included:

```graphql
fragment userProfileFields on User {
    id
    username
    slug
}

query GetUserProfile($id: ID!) {
    user(id: $id) {
        ...userProfileFields
    }
}
```

In the above example fragment `userProfileFields` is used to specify a list of fields for the `User` type in the `GetUserProfile` query, but outside the `query { ... }` body itself.

Fragments can also be used in other fragments, and used multiple times within a query:

```graphql
fragment threadsListUserFields on User {
    id
    username
    slug
}

fragment threadsListThreadFields on Thread {
    id
    title
    slug
    starter {
        ...threadsListUserFields
    }
    poster {
        ...threadsListUserFields
    }
}

query GetCategoryThreads($category: ID!) {
    threads(category: $category) {
        edge {
            node {
                ...threadsListThreadFields
            }
            cursor
        }
        hasMore
    }
}
```

The `threadsListUserFields` fragment is used to specify fields for `User` type to query in `User` fields of `Thread` type, itself queried for in the `GetCategoryThreads` operation.

Fragments can be used in queries, mutations and subscriptions.

While it is not a syntax error to define a GraphQL fragment in `schema.graphql`, such fragments are discarded from the final GraphQL schema and can't be used in queries.
