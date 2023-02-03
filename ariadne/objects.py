from typing import Callable, Dict, Optional, cast

from graphql.type import GraphQLNamedType, GraphQLObjectType, GraphQLSchema

from .resolvers import resolve_to
from .types import Resolver, SchemaBindable


class ObjectType(SchemaBindable):
    """Bindable populating object types in a GraphQL schema with Python logic.

    # Example

    Following code creates a GraphQL schema with single object type named `Query`
    and uses `ObjectType` to set resolvers on its fields:

    ```python
    import random
    from datetime import datetime

    from ariadne import ObjectType, make_executable_schema

    query_type = ObjectType("Query")

    @query_type.field("diceRoll")
    def resolve_dice_roll(*_):
        return random.int(1, 6)


    @query_type.field("year")
    def resolve_year(*_):
        return datetime.today().year


    schema = make_executable_schema(
        \"\"\"
        type Query {
            diceRoll: Int!
            year: Int!
        }
        \"\"\",
        query_type,
    )
    ```


    # Example with objects in objects

    When a field in the schema returns other GraphQL object, this object's
    resolvers are called with value returned from field's resolver. For example
    if there's an `user` field on the `Query` type that returns the `User` type,
    you don't have to resolve `User` fields in `user` resolver. In below example
    `fullName` field on `User` type is resolved from data on `UserModel` object
    that `user` field resolver on `Query` type returned:

    ```python
    import dataclasses
    from ariadne import ObjectType, make_executable_schema

    @dataclasses.dataclass
    class UserModel:
        id: int
        username: str
        first_name: str
        last_name: str


    users = [
        UserModel(
            id=1,
            username="Dany",
            first_name="Daenerys",
            last_name="Targaryen",
        ),
        UserModel(
            id=2,
            username="BlackKnight19",
            first_name="Cahir",
            last_name="Mawr Dyffryn aep Ceallach",
        ),
        UserModel(
            id=3,
            username="TheLady",
            first_name="Dorotea",
            last_name="Senjak",
        ),
    ]


    # Query type resolvers return users, but don't care about fields
    # of User type
    query_type = ObjectType("Query")

    @query_type.field("users")
    def resolve_users(*_) -> list[UserModel]:
        # In real world applications this would be a database query
        # returning iterable with user results
        return users


    @query_type.field("user")
    def resolve_user(*_, id: str) -> UserModel | None:
        # In real world applications this would be a database query
        # returning single user or None

        try:
            # GraphQL ids are always strings
            clean_id = int(id)
        except (ValueError, TypeError):
            # We could raise "ValueError" instead
            return None

        for user in users:
            if user.id == id:
                return user

        return None


    # User type resolvers don't know how to retrieve User, but know how to
    # resolve User type fields from UserModel instance
    user_type = ObjectType("User")

    # Resolve "name" GraphQL field to "username" attribute
    user_type.set_alias("name", "username")

    # Resolve "fullName" field to combined first and last name
    # `obj` argument will be populated by GraphQL with a value from
    # resolver for field returning "User" type
    @user_type.field("fullName")
    def resolve_user_full_name(obj: UserModel, *_):
        return f"{obj.first_name} {obj.last_name}"


    schema = make_executable_schema(
        \"\"\"
        type Query {
            users: [User!]!
            user(id: ID!): User
        }

        type User {
            id: ID!
            name: String!
            fullName: String!
        }
        \"\"\",
        query_type,
        user_type,
    )
    ```
    """

    _resolvers: Dict[str, Resolver]

    def __init__(self, name: str) -> None:
        """Initializes the `ObjectType` with a `name`.

        # Required arguments

        `name`: a `str` with the name of GraphQL object type in GraphQL schema to
        bind to.
        """
        self.name = name
        self._resolvers = {}

    def field(self, name: str) -> Callable[[Resolver], Resolver]:
        """Return a decorator that sets decorated function as a resolver for named field.

        Wrapper for `create_register_resolver` that on runtime validates `name` to be a
        string.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        bind decorated resolver to.
        """
        if not isinstance(name, str):
            raise ValueError(
                'field decorator should be passed a field name: @foo.field("name")'
            )
        return self.create_register_resolver(name)

    def create_register_resolver(self, name: str) -> Callable[[Resolver], Resolver]:
        """Return a decorator that sets decorated function as a resolver for named field.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        bind decorated resolver to.
        """

        def register_resolver(f: Resolver) -> Resolver:
            self._resolvers[name] = f
            return f

        return register_resolver

    def set_field(self, name, resolver: Resolver) -> Resolver:
        """Set a resolver for the field name.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        set this resolver for.

        `resolver`: a `Resolver` function to use.
        """
        self._resolvers[name] = resolver
        return resolver

    def set_alias(self, name: str, to: str) -> None:
        """Set an alias resolver for the field name to given Python nme.

        # Required arguments

        `name`: a `str` with a name of the GraphQL object's field in GraphQL schema to
        set this resolver for.

        `to`: a `str` of an attribute or dict key to resolve this field to.
        """
        self._resolvers[name] = resolve_to(to)

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `ObjectType` instance to the instance of GraphQL schema.

        If it has any resolver functions set, it assigns those to GraphQL type's
        fields `resolve` attributes. If field already has other resolver set on
        its `resolve` attribute, this resolver is replaced with the new one.
        """
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLObjectType, graphql_type)
        self.bind_resolvers_to_graphql_type(graphql_type)

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        """Validates that schema's GraphQL type associated with this `ObjectType`
        is a `type`."""
        if not graphql_type:
            raise ValueError("Type %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLObjectType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLObjectType.__name__)
            )

    def bind_resolvers_to_graphql_type(self, graphql_type, replace_existing=True):
        """Binds this `ObjectType` instance to the instance of GraphQL schema."""
        for field, resolver in self._resolvers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )
            if graphql_type.fields[field].resolve is None or replace_existing:
                graphql_type.fields[field].resolve = resolver


class QueryType(ObjectType):
    """An convenience class for defining Query type.

    # Example

    Both of those code samples have same effect:

    ```python
    query_type = QueryType()
    ```

    ```python
    query_type = ObjectType("Query")
    ```
    """

    def __init__(self) -> None:
        """Initializes the `QueryType` with a GraphQL name set to `Query`."""
        super().__init__("Query")


class MutationType(ObjectType):
    """An convenience class for defining Mutation type.

    # Example

    Both of those code samples have same result:

    ```python
    mutation_type = MutationType()
    ```

    ```python
    mutation_type = ObjectType("Mutation")
    ```
    """

    def __init__(self) -> None:
        """Initializes the `MutationType` with a GraphQL name set to `Mutation`."""
        super().__init__("Mutation")
