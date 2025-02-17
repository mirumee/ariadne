from typing import Optional, cast

from graphql.type import GraphQLNamedType, GraphQLSchema, GraphQLUnionType

from .types import Resolver, SchemaBindable


class UnionType(SchemaBindable):
    """Bindable populating interfaces in a GraphQL schema with Python logic.


    # Type resolver

    Because GraphQL fields using union as their returning type can return any
    Python value from their resolver, GraphQL unions require special type of
    resolver called "type resolver" to function.

    This resolver is called with the value returned by field's resolver and is
    required to return a string with a name of GraphQL type represented by Python
    value from the field:

    ```python
    def example_type_resolver(obj: Any, *_) -> str:
        if isinstance(obj, PythonReprOfUser):
            return "USer"

        if isinstance(obj, PythonReprOfComment):
            return "Comment"

        raise ValueError(f"Don't know GraphQL type for '{obj}'!")
    ```

    This resolver is not required if the GraphQL field returns a value that has
    the `__typename` attribute or `dict` key with a name of the GraphQL type:

    ```python
    user_data_dict = {"__typename": "User", ...}

    # or...

    class UserRepr:
        __typename: str = "User"
    ```

    # Example

    Following code creates a GraphQL schema with a field that returns random
    result of either `User` or `Post` GraphQL type. It also supports dict with
    `__typename` key that explicitly declares its GraphQL type:

    ```python
    import random
    from dataclasses import dataclass
    from ariadne import QueryType, UnionType, make_executable_schema

    @dataclass
    class UserModel:
        id: str
        name: str

    @dataclass
    class PostModel:
        id: str
        message: str

    results = (
        UserModel(id=1, name="Bob"),
        UserModel(id=2, name="Alice"),
        UserModel(id=3, name="Jon"),
        PostModel(id=1, message="Hello world!"),
        PostModel(id=2, message="How's going?"),
        PostModel(id=3, message="Sure thing!"),
        {"__typename": "User", "id": 4, "name": "Polito"},
        {"__typename": "User", "id": 5, "name": "Aerith"},
        {"__typename": "Post", "id": 4, "message": "Good day!"},
        {"__typename": "Post", "id": 5, "message": "Whats up?"},
    )

    query_type = QueryType()

    @query_type.field("result")
    def resolve_random_result(*_):
        return random.choice(results)


    result_type = UnionType("Result")

    @result_type.type_resolver
    def resolve_result_type(obj: UserModel | PostModel | dict, *_) -> str:
        if isinstance(obj, UserModel):
            return "User"

        if isinstance(obj, PostModel):
            return "Post"

        if isinstance(obj, dict) and obj.get("__typename"):
            return obj["__typename"]

        raise ValueError(f"Don't know GraphQL type for '{obj}'!")


    schema = make_executable_schema(
        \"\"\"
        type Query {
            result: Result!
        }

        union Result = User | Post

        type User {
            id: ID!
            name: String!
        }

        type Post {
            id: ID!
            message: String!
        }
        \"\"\",
        query_type,
        result_type,
    )
    ```
    """

    _resolve_type: Optional[Resolver]

    def __init__(self, name: str, type_resolver: Optional[Resolver] = None) -> None:
        """Initializes the `UnionType` with a `name` and optional `type_resolver`.

        Type resolver is required by `UnionType` to function properly, but can
        be set later using either `set_type_resolver(type_resolver)`
        setter or `type_resolver` decorator.

        # Required arguments

        `name`: a `str` with the name of GraphQL union type in GraphQL schema to
        bind to.

        # Optional arguments

        `type_resolver`: a `Resolver` used to resolve a str with name of GraphQL type
        from it's Python representation.
        """
        self.name = name
        self._resolve_type = type_resolver

    def set_type_resolver(self, type_resolver: Resolver) -> Resolver:
        """Sets function as type resolver for this union.

        Can be used as a decorator. Also available through `type_resolver` alias:

        ```python
        union_type = UnionType("MyUnion")


        @union_type.type_resolver
        def type_resolver(obj: Any, *_) -> str: ...
        ```
        """
        self._resolve_type = type_resolver
        return type_resolver

    # Alias type resolver for consistent decorator API
    type_resolver = set_type_resolver

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `UnionType` instance to the instance of GraphQL schema.

        Sets `resolve_type` attribute on GraphQL union. If this attribute was
        previously set, it will be replaced to new value.
        """
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLUnionType, graphql_type)
        graphql_type.resolve_type = self._resolve_type

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        """Validates that schema's GraphQL type associated with this `UnionType`
        is an `union`."""
        if not graphql_type:
            raise ValueError(f"Type {self.name} is not defined in the schema")
        if not isinstance(graphql_type, GraphQLUnionType):
            raise ValueError(
                f"{self.name} is defined in the schema, "
                f"but it is instance of {type(graphql_type).__name__} "
                f"(expected {GraphQLUnionType.__name__})"
            )
