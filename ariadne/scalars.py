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
    _serialize: Optional[GraphQLScalarSerializer]
    _parse_value: Optional[GraphQLScalarValueParser]
    _parse_literal: Optional[GraphQLScalarLiteralParser]

    def __init__(
        self,
        name: str,
        *,
        serializer: GraphQLScalarSerializer = None,
        value_parser: GraphQLScalarValueParser = None,
        literal_parser: GraphQLScalarLiteralParser = None,
    ) -> None:
        self.name = name
        self._serialize = serializer
        self._parse_value = value_parser
        self._parse_literal = literal_parser

    def set_serializer(self, f: GraphQLScalarSerializer) -> GraphQLScalarSerializer:
        self._serialize = f
        return f

    def set_value_parser(self, f: GraphQLScalarValueParser) -> GraphQLScalarValueParser:
        self._parse_value = f
        return f

    def set_literal_parser(
        self, f: GraphQLScalarLiteralParser
    ) -> GraphQLScalarLiteralParser:
        self._parse_literal = f
        return f

    # Alias above setters for consistent decorator API
    serializer = set_serializer
    value_parser = set_value_parser
    literal_parser = set_literal_parser

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
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
        if not graphql_type:
            raise ValueError("Scalar %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLScalarType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLScalarType.__name__)
            )
