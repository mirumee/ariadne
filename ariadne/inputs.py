from typing import Optional, cast

from graphql import GraphQLInputObjectType, GraphQLSchema
from graphql.type.definition import GraphQLInputFieldOutType, GraphQLNamedType

from .types import SchemaBindable


class InputType(SchemaBindable):
    """Bindable populating input types in a GraphQL schema with Python logic.

    # Example input value represented as dataclass

    Following code creates a GraphQL schema with object type named `Query`
    with single field which has an argument of an input type. It then uses
    the `InputType` to set `ExampleInput` dataclass as Python representation
    of this GraphQL type:

    ```python
    from dataclasses import dataclass

    from ariadne import InputType, QueryType, make_executable_schema

    @dataclass
    class ExampleInput:
        id: str
        message: str

    query_type = QueryType()

    @query_type.field("repr")
    def resolve_repr(*_, input: ExampleInput):
        return repr(input)

    schema = make_executable_schema(
        \"\"\"
        type Query {
            repr(input: ExampleInput): String!
        }

        input ExampleInput {
            id: ID!
            message: String!
        }
        \"\"\",
        query_type,
        # Lambda is used because out type (second argument of InputType)
        # is called with single dict and dataclass requires each value as
        # separate argument.
        InputType("ExampleInput", lambda data: ExampleInput(**data)),
    )
    ```

    # Example input with its fields mapped to custom dict keys

    Following code creates a GraphQL schema with object type named `Query`
    with single field which has an argument of an input type. It then uses
    the `InputType` to set custom "out names" values, mapping GraphQL
    `shortMessage` to `message` key in Python dict:

    ```python
    from ariadne import InputType, QueryType, make_executable_schema

    query_type = QueryType()

    @query_type.field("repr")
    def resolve_repr(*_, input: dict):
        # Dict will have `id` and `message` keys
        input_id = input["id"]
        input_message = input["message"]
        return f"id: {input_id}, message: {input_message}"

    schema = make_executable_schema(
        \"\"\"
        type Query {
            repr(input: ExampleInput): String!
        }

        input ExampleInput {
            id: ID!
            shortMessage: String!
        }
        \"\"\",
        query_type,
        InputType("ExampleInput", out_names={"shortMessage": "message"}),
    )
    ```

    # Example input value as dataclass with custom named fields

    Following code creates a GraphQL schema with object type named `Query`
    with single field which has an argument of an input type. It then uses
    the `InputType` to set `ExampleInput` dataclass as Python representation
    of this GraphQL type, and maps `shortMessage` input field to it's
    `message` attribute:

    ```python
    from dataclasses import dataclass

    from ariadne import InputType, QueryType, make_executable_schema

    @dataclass
    class ExampleInput:
        id: str
        message: str

    query_type = QueryType()

    @query_type.field("repr")
    def resolve_repr(*_, input: ExampleInput):
        return repr(input)

    schema = make_executable_schema(
        \"\"\"
        type Query {
            repr(input: ExampleInput): String!
        }

        input ExampleInput {
            id: ID!
            shortMessage: String!
        }
        \"\"\",
        query_type,
        InputType(
            "ExampleInput",
            lambda data: ExampleInput(**data),
            {"shortMessage": "message"},
        ),
    )
    ```
    """

    _out_type: Optional[GraphQLInputFieldOutType]
    _out_names: Optional[dict[str, str]]

    def __init__(
        self,
        name: str,
        out_type: Optional[GraphQLInputFieldOutType] = None,
        out_names: Optional[dict[str, str]] = None,
    ) -> None:
        """Initializes the `InputType` with a `name` and optionally out type
        and out names.

        # Required arguments

        `name`: a `str` with the name of GraphQL object type in GraphQL schema to
        bind to.

        # Optional arguments

        `out_type`: a `GraphQLInputFieldOutType`, Python callable accepting single
        argument, a dict with data from GraphQL query, required to return
        a Python representation of input type.

        `out_names`: a `Dict[str, str]` with mappings from GraphQL field names
        to dict keys in a Python dictionary used to contain a data passed as
        input.
        """
        self.name = name
        self._out_type = out_type
        self._out_names = out_names

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `InputType` instance to the instance of GraphQL schema.

        if it has an out type function, it assigns it to GraphQL type's
        `out_type` attribute. If type already has other function set on
        it's `out_type` attribute, this type is replaced with new one.

        If it has any out names set, it assigns those to GraphQL type's
        fields `out_name` attributes. If field already has other out name set on
        its `out_name` attribute, this name is replaced with the new one.
        """
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLInputObjectType, graphql_type)

        if self._out_type:
            graphql_type.out_type = self._out_type  # type: ignore

        if self._out_names:
            for graphql_name, python_name in self._out_names.items():
                if graphql_name not in graphql_type.fields:
                    raise ValueError(
                        f"Field {graphql_name} is not defined on type {self.name}"
                    )
                graphql_type.fields[graphql_name].out_name = python_name

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        """Validates that schema's GraphQL type associated with this `InputType`
        is an `input`."""
        if not graphql_type:
            raise ValueError(f"Type {self.name} is not defined in the schema")
        if not isinstance(graphql_type, GraphQLInputObjectType):
            raise ValueError(
                f"{self.name} is defined in the schema, "
                f"but it is instance of {type(graphql_type).__name__} "
                f"(expected {GraphQLInputObjectType.__name__})"
            )
