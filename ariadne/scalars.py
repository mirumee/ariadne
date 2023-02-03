from typing import Optional, cast

from graphql.type import (
    GraphQLNamedType,
    GraphQLScalarLiteralParser,
    GraphQLScalarSerializer,
    GraphQLScalarType,
    GraphQLScalarValueParser,
    GraphQLSchema,
)

from .types import SchemaBindable


class ScalarType(SchemaBindable):
    """Bindable populating scalars in a GraphQL schema with Python logic.

    GraphQL scalars implement default serialization and deserialization logic.
    This class is only useful when custom logic is needed, most commonly
    when Python representation of scalar's value is not JSON-serializable by
    default.

    This logic can be customized for three steps:

    # Serialization

    Serialization step converts Python representation of scalar's value to a
    JSON serializable format.

    Serializer function takes single argument and returns a single,
    JSON serializable value:

    ```python
    def serialize_date(value: date) -> str:
        # Serialize dates as "YYYY-MM-DD" string
        return date.strftime("%Y-%m-%d")
    ```

    # Value parsing

    Value parsing step converts value from deserialized JSON
    to Python representation.

    Value parser function takes single argument and returns a single value:

    ```python
    def parse_date_str(value: str) -> date:
        try:
            # Parse "YYYY-MM-DD" string into date
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError(
                f'"{value}" is not a date string in YYYY-MM-DD format.'
            )
    ```

    # Literal parsing

    Literal parsing step converts value from GraphQL abstract syntax tree (AST)
    to Python representation.

    Literal parser function takes two arguments, an AST node and a dict with
    query's variables and returns Python value:

    ```python
    def parse_date_literal(
        value: str, variable_values: dict[str, Any] = None
    ) -> date:
        if not isinstance(ast, StringValueNode):
            raise ValueError()

        try:
            # Parse "YYYY-MM-DD" string into date
            return datetime.strptime(ast.value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError(
                f'"{value}" is not a date string in YYYY-MM-DD format.'
            )
    ```

    When scalar has custom value parser set, but not the literal parser, the
    GraphQL query executor will use default literal parser, and then call the
    value parser with it's return value. This mechanism makes custom literal
    parser unnecessary for majority of scalar implementations.

    Scalar literals are always parsed twice: on query validation and during
    query execution.

    # Example datetime scalar

    Following code defines a datetime scalar which converts Python datetime
    object to and from a string. Note that it without custom literal scalar:

    ```python
    from datetime import datetime

    from ariadne import QueryType, ScalarType, make_executable_schema

    scalar_type = ScalarType("DateTime")

    @scalar_type.serializer
    def serialize_value(val: datetime) -> str:
        return datetime.strftime(val, "%Y-%m-%d %H:%M:%S")


    @scalar_type.value_parser
    def parse_value(val) -> datetime:
        if not isinstance(val, str):
            raise ValueError(
                f"'{val}' is not a valid JSON representation "
            )

        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")


    query_type = QueryType()

    @query_type.field("now")
    def resolve_now(*_):
        return datetime.now()


    @query_type.field("diff")
    def resolve_diff(*_, value):
        delta = datetime.now() - value
        return int(delta.total_seconds())


    schema = make_executable_schema(
        \"\"\"
        scalar DateTime

        type Query {
            now: DateTime!
            diff(value: DateTime): Int!
        }
        \"\"\",
        scalar_type,
        query_type,
    )
    ```

    # Example generic scalar

    Generic scalar is a pass-through scalar that doesn't perform any value
    conversion. Most common use case for those is for GraphQL fields that
    return unstructured JSON to the client. To create a scalar like this,
    you can simply include  `scalar Generic` in your GraphQL schema:

    ```python
    from ariadne import QueryType, make_executable_schema

    query_type = QueryType()

    @query_type.field("rawJSON")
    def resolve_raw_json(*_):
        # Note: this value needs to be JSON serializable
        return {
            "map": {
                "0": "Hello!",
                "1": "World!",
            },
            "list": [
                2,
                1,
                3,
                7,
            ],
        }


    schema = make_executable_schema(
        \"\"\"
        scalar Generic

        type Query {
            rawJSON: Generic!
        }
        \"\"\",
        query_type,
    )
    ```
    """

    _serialize: Optional[GraphQLScalarSerializer]
    _parse_value: Optional[GraphQLScalarValueParser]
    _parse_literal: Optional[GraphQLScalarLiteralParser]

    def __init__(
        self,
        name: str,
        *,
        serializer: Optional[GraphQLScalarSerializer] = None,
        value_parser: Optional[GraphQLScalarValueParser] = None,
        literal_parser: Optional[GraphQLScalarLiteralParser] = None,
    ) -> None:
        """Initializes the `ScalarType` with a `name`.

        # Required arguments

        `name`: a `str` with the name of GraphQL scalar in GraphQL schema to
        bind to.

        # Optional arguments

        `serializer`: a function called to convert Python representation of
        scalar's value to JSON serializable format.

        `value_parser`: a function called to convert a JSON deserialized value
        from query's "variables" JSON into scalar's Python representation.

        `literal_parser`: a function called to convert an AST value
        from parsed query into scalar's Python representation.
        """
        self.name = name
        self._serialize = serializer
        self._parse_value = value_parser
        self._parse_literal = literal_parser

    def set_serializer(self, f: GraphQLScalarSerializer) -> GraphQLScalarSerializer:
        """Sets function as serializer for this scalar.

        Can be used as a decorator. Also available through `serializer` alias:

        ```python
        date_scalar = ScalarType("Date")

        @date_scalar.serializer
        def serialize_date(value: date) -> str:
            # Serialize dates as "YYYY-MM-DD" string
            return date.strftime("%Y-%m-%d")
        ```
        """
        self._serialize = f
        return f

    def set_value_parser(self, f: GraphQLScalarValueParser) -> GraphQLScalarValueParser:
        """Sets function as value parser for this scalar.

        Can be used as a decorator. Also available through `value_parser` alias:

        ```python
        date_scalar = ScalarType("Date")

        @date_scalar.value_parser
        def parse_date_str(value: str) -> date:
            try:
                # Parse "YYYY-MM-DD" string into date
                return datetime.strptime(value, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                raise ValueError(
                    f'"{value}" is not a date string in YYYY-MM-DD format.'
                )
        ```
        """
        self._parse_value = f
        return f

    def set_literal_parser(
        self, f: GraphQLScalarLiteralParser
    ) -> GraphQLScalarLiteralParser:
        """Sets function as literal parser for this scalar.

        Can be used as a decorator. Also available through `literal_parser` alias:

        ```python
        date_scalar = ScalarType("Date")

        @date_scalar.literal_parser
        def parse_date_literal(
            value: str, variable_values: Optional[dict[str, Any]] = None
        ) -> date:
            if not isinstance(ast, StringValueNode):
                raise ValueError()

            try:
                # Parse "YYYY-MM-DD" string into date
                return datetime.strptime(ast.value, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                raise ValueError(
                    f'"{value}" is not a date string in YYYY-MM-DD format.'
                )
        ```
        """
        self._parse_literal = f
        return f

    # Alias above setters for consistent decorator API
    serializer = set_serializer
    value_parser = set_value_parser
    literal_parser = set_literal_parser

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `ScalarType` instance to the instance of GraphQL schema.

        If it has serializer or parser functions set, it assigns those to GraphQL
        scalar's attributes. If scalar's attribute already has other function
        set, this function is replaced with the new one.
        """
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLScalarType, graphql_type)

        if self._serialize:
            # See mypy bug https://github.com/python/mypy/issues/2427
            graphql_type.serialize = self._serialize  # type: ignore
        if self._parse_value:
            graphql_type.parse_value = self._parse_value  # type: ignore
        if self._parse_literal:
            graphql_type.parse_literal = self._parse_literal  # type: ignore

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        """Validates that schema's GraphQL type associated with this `ScalarType`
        is a `scalar`."""
        if not graphql_type:
            raise ValueError("Scalar %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLScalarType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLScalarType.__name__)
            )
