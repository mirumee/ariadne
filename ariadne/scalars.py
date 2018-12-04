from typing import Optional

from graphql.type import GraphQLScalarType, GraphQLSchema

from .types import Bindable, ScalarOperation


class Scalar(Bindable):
    _serialize: Optional[ScalarOperation]
    _parse_value: Optional[ScalarOperation]
    _parse_literal: Optional[ScalarOperation]

    def __init__(self, name: str) -> None:
        self.name = name
        self._serialize = None
        self._parse_value = None
        self._parse_literal = None

    def serializer(self, f: ScalarOperation) -> ScalarOperation:
        self._serialize = f
        return f

    def value_parser(self, f: ScalarOperation) -> ScalarOperation:
        self._parse_value = f
        return f

    def literal_parser(self, f: ScalarOperation) -> ScalarOperation:
        self._parse_literal = f
        return f

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)

        if self._serialize:
            graphql_type.serialize = self._serialize
        if self._parse_value:
            graphql_type.parse_value = self._parse_value
        if self._parse_literal:
            graphql_type.parse_literal = self._parse_literal

    def validate_graphql_type(self, graphql_type) -> None:
        if not graphql_type:
            raise ValueError("Scalar %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLScalarType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLScalarType.__name__)
            )
