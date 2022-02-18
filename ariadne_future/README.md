# `ariadne_future` package

This package contains experimental future Ariadne API implementation that is intended to replace current procedural approach.

For reasoning behind this work, please see [this GitHub discussion](https://github.com/mirumee/ariadne/issues/306).


## `ObjectType`

New `ObjectType` is base class for Python classes representing GraphQL types (either `type` or `extend type`).


### `__schema__`

`ObjectType` key attribute is `__schema__` string that can define only one GraphQL type:

```python
class QueryType(ObjectType):
    __schema__ = """
    type Query {
        year: Int!
    }
    """
```

`ObjectType` implements validation logic for `__schema__`. It verifies that its valid SDL string defining exactly one GraphQL type, and raises error otherwise. 


### Resolvers

Resolvers are class methods or static methods named after schema's fields:

```python
class QueryType(ObjectType):
    __schema__ = """
    type Query {
        year: Int!
    }
    """

    @staticmethod
    def year(_, info: GraphQLResolveInfo) -> int:
        return 2022
```

> `ObjectType` could look up return type of `Int` scalar's `serialize` method and compare it with resolver's return type as extra safety net.

If resolver function is not present for field, default resolver implemented by `graphql-core` will be used in its place.

In situations when field's name should be resolved to different value, custom mappings can be defined via `__resolvers__` attribute:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
    }
    """
    __resolvers__ = {
        "dateJoined": "date_joined"
    }
```

Above code will result in Ariadne generating resolver resolving "dateJoined" field to "date_joined" attribute on resolved object.

If `date_joined` exists as callable on `ObjectType`, it will be used as resolver for `dateJoined`:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String
    }
    """
    __resolvers__ = {
        "dateJoined": "date_joined"
    }

    @staticmethod
    def date_joined(user, info) -> Optional[str]:
        if can_see_activity(info.context):
            return user.date_joined

        return None
```

> `ObjectType` could raise error if resolver can't be matched to any field on type.


### `__requires__`

When GraphQL type requires on other GraphQL type (or scalar/directive etc. ect.) `ObjectType` will raise an error about missing dependency. This dependency can be provided through `__requires__` attribute:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
    }
    """


class UsersGroupType(ObjectType):
    __schema__ = """
    type UsersGroup {
        id: ID!
        users: [User!]!
    }
    """
    __requires__ = [UserType]
```

`ObjectType` verifies that types specified in `__requires__` actually define required types. If `__schema__` in `UserType` is not defining `User`, error will be raised about missing dependency.

In case of circular dependencies, special `DeferredType` can be used:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        dateJoined: String!
        group: UsersGroup
    }
    """
    __requires__ = [DeferredType("UsersGroup")]


class UsersGroupType(ObjectType):
    __schema__ = """
    type UsersGroup {
        id: ID!
        users: [User!]!
    }
    """
    __requires__ = [UserType]
```

`DeferredType` makes `UserType` happy about `UsersGroup` dependency, deferring dependency check to `make_executable_schema`. If "real" `UsersGroup` is not provided at that time, error will be raised about missing types required to create schema.


## `make_executable_schema`

New `make_executable_schema` takes list of Ariadne's types and constructs executable schema from them, performing last-stage validation for types consistency:

```python
class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        username: String!
    }
    """


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        user: User
    }
    """
    __requires__ = [UserType]

    @staticmethod
    def user(*_):
        return {
            "id": 1,
            "username": "Alice",
        }


schema = make_executable_schema(QueryType)
```
