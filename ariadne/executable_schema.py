from typing import Dict, List, Optional, Type, Union

from graphql import (
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    parse,
)

from .enums import (
    EnumType,
    set_default_enum_values_on_schema,
    validate_schema_enum_values,
)
from .schema_names import SchemaNameConverter, convert_schema_names
from .schema_visitor import SchemaDirectiveVisitor
from .types import SchemaBindable


def make_executable_schema(
    type_defs: Union[str, List[str]],
    *bindables: Union[SchemaBindable, List[SchemaBindable]],
    directives: Optional[Dict[str, Type[SchemaDirectiveVisitor]]] = None,
    convert_names_case: Union[bool, SchemaNameConverter] = False,
) -> GraphQLSchema:
    """Create a `GraphQLSchema` instance that can be used to execute queries.

    Returns a `GraphQLSchema` instance with attributes populated with Python
    values and functions.

    # Required arguments

    `type_defs`: a `str` or list of `str` with GraphQL types definitions in
    schema definition language (`SDL`).

    # Optional arguments

    `bindables`: instances or lists of instances of schema bindables. Order in
    which bindables are passed to `make_executable_schema` matters depending on
    individual bindable's implementation.

    `directives`: a dict of GraphQL directives to apply to schema. Dict's keys must
    correspond to directives names in GraphQL schema and values should be
    `SchemaDirectiveVisitor` classes (_not_ instances) implementing their logic.

    `convert_names_case`: a `bool` or function of `SchemaNameConverter` type to
    use to convert names in GraphQL schema between `camelCase` used by GraphQL
    and `snake_case` used by Python. Defaults to `False`, making all conversion
    explicit and up to developer to implement. Set `True` to use
    default strategy using `convert_camel_case_to_snake` for name conversions or
    set to custom function to customize this behavior.

    # Example with minimal schema

    Below code creates minimal executable schema that doesn't implement any Python
    logic, but still executes queries using `root_value`:

    ```python
    from ariadne import graphql_sync, make_executable_schema

    schema = make_executable_schema(
        \"\"\"
        type Query {
            helloWorld: String!
        }
        \"\"\"
    )

    no_errors, result = graphql_sync(
        schema,
        {"query": "{ helloWorld }"},
        root_value={"helloWorld": "Hello world!"},
    )

    assert no_errors
    assert result == {
        "data": {
            "helloWorld": "Hello world!",
        },
    }
    ```

    # Example with bindables

    Below code creates executable schema that combines different ways of passing
    bindables to add Python logic to schema:

    ```python
    from dataclasses import dataclass
    from ariadne import ObjectType, QueryType, UnionType, graphql_sync, make_executable_schema

    # Define some types representing database models in real applications
    @dataclass
    class UserModel:
        id: str
        name: str

    @dataclass
    class PostModel:
        id: str
        body: str

    # Create fake "database"
    results = (
        UserModel(id=1, name="Bob"),
        UserModel(id=2, name="Alice"),
        UserModel(id=3, name="Jon"),
        PostModel(id=1, body="Hello world!"),
        PostModel(id=2, body="How's going?"),
        PostModel(id=3, body="Sure thing!"),
    )


    # Resolve username field in GraphQL schema to user.name attribute
    user_type = ObjectType("User")
    user_type.set_alias("username", "name")


    # Resolve message field in GraphQL schema to post.body attribute
    post_type = ObjectType("Post")
    post_type.set_alias("message", "body")


    # Resolve results field in GraphQL schema to results array
    query_type = QueryType()

    @query_type.field("results")
    def resolve_results(*_):
        return results


    # Resolve GraphQL type of individual result from it's Python class
    result_type = UnionType("Result")

    @result_type.type_resolver
    def resolve_result_type(obj: UserModel | PostModel | dict, *_) -> str:
        if isinstance(obj, UserModel):
            return "User"

        if isinstance(obj, PostModel):
            return "Post"

        raise ValueError(f"Don't know GraphQL type for '{obj}'!")


    # Create executable schema that returns list of results
    schema = make_executable_schema(
        \"\"\"
        type Query {
            results: [Result!]!
        }

        union Result = User | Post

        type User {
            id: ID!
            username: String!
        }

        type Post {
            id: ID!
            message: String!
        }
        \"\"\",
        # Bindables *args accept single instances:
        query_type,
        result_type,
        # Bindables *args accepts lists of instances:
        [user_type, post_type],
        # Both approaches can be mixed
    )

    # Query the schema for results
    no_errors, result = graphql_sync(
        schema,
        {
            "query": (
                \"\"\"
                {
                    results {
                        ... on Post {
                            id
                            message
                        }
                        ... on User {
                            id
                            username
                        }
                    }
                }
                \"\"\"
            ),
        },
    )

    # Verify that it works
    assert no_errors
    assert result == {
        "data": {
            "results": [
                {
                    "id": "1",
                    "username": "Bob",
                },
                {
                    "id": "2",
                    "username": "Alice",
                },
                {
                    "id": "3",
                    "username": "Jon",
                },
                {
                    "id": "1",
                    "message": "Hello world!",
                },
                {
                    "id": "2",
                    "message": "How's going?",
                },
                {
                    "id": "3",
                    "message": "Sure thing!",
                },
            ],
        },
    }
    ```

    # Example with directive

    Below code uses `directives` option to set custom directive on schema:

    ```python
    from functools import wraps
    from ariadne import SchemaDirectiveVisitor, graphql_sync, make_executable_schema
    from graphql import default_field_resolver

    class UppercaseDirective(SchemaDirectiveVisitor):
        def visit_field_definition(self, field, object_type):
            org_resolver = field.resolve or default_field_resolver

            @wraps(org_resolver)
            def uppercase_resolved_value(*args, **kwargs):
                value = org_resolver(*args, **kwargs)
                if isinstance(value, str):
                    return value.upper()
                return value

            # Extend field's behavior by wrapping it's resolver in custom one
            field.resolve = uppercase_resolved_value
            return field


    schema = make_executable_schema(
        \"\"\"
        directive @uppercase on FIELD_DEFINITION

        type Query {
            helloWorld: String! @uppercase
        }
        \"\"\",
        directives={"uppercase": UppercaseDirective},
    )

    no_errors, result = graphql_sync(
        schema,
        {"query": "{ helloWorld }"},
        root_value={"helloWorld": "Hello world!"},
    )

    assert no_errors
    assert result == {
        "data": {
            "helloWorld": "HELLO WORLD!",
        },
    }
    ```

    # Example with converted names

    Below code uses `convert_names_case=True` option to resolve `helloWorld`
    field to `hello_world` key from `root_value`:

    ```python
    from ariadne import graphql_sync, make_executable_schema

    schema = make_executable_schema(
        \"\"\"
        type Query {
            helloWorld: String!
        }
        \"\"\",
        convert_names_case=True,
    )

    no_errors, result = graphql_sync(
        schema,
        {"query": "{ helloWorld }"},
        root_value={"hello_world": "Hello world!"},
    )

    assert no_errors
    assert result == {
        "data": {
            "helloWorld": "Hello world!",
        },
    }
    ```
    """

    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    ast_document = parse(type_defs)
    schema = build_ast_schema(ast_document)
    flat_bindables: List[SchemaBindable] = flatten_bindables(*bindables)

    for bindable in flat_bindables:
        bindable.bind_to_schema(schema)

    set_default_enum_values_on_schema(schema)

    if directives:
        SchemaDirectiveVisitor.visit_schema_directives(schema, directives)

    assert_valid_schema(schema)
    validate_schema_enum_values(schema)
    repair_default_enum_values(schema, flat_bindables)

    if convert_names_case:
        convert_schema_names(
            schema,
            convert_names_case if callable(convert_names_case) else None,
        )

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def flatten_bindables(
    *bindables: Union[SchemaBindable, List[SchemaBindable]]
) -> List[SchemaBindable]:
    new_bindables = []

    for bindable in bindables:
        if isinstance(bindable, list):
            new_bindables.extend(bindable)
        else:
            new_bindables.append(bindable)

    return new_bindables


def repair_default_enum_values(schema, bindables) -> None:
    for bindable in bindables:
        if isinstance(bindable, EnumType):
            bindable.bind_to_default_values(schema)
