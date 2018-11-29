from graphql.type import GraphQLScalarType, GraphQLSchema


class Scalar:
    def __init__(self, name):
        self.name = name
        self._serialize = None
        self._parse_value = None
        self._parse_literal = None

    def serializer(self, f):
        self._serialize = f
        return f

    def value_parser(self, f):
        self._parse_value = f
        return f

    def literal_parser(self, f):
        self._parse_literal = f
        return f

    def bind_to_schema(self, schema: GraphQLSchema):
        graphql_type = schema.type_map.get(self.name)
        if not graphql_type:
            raise ValueError("Scalar %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLScalarType):
            raise ValueError(
                "%s is defined in schema, but it is not a scalar" % self.name
            )

        if self._serialize:
            graphql_type.serialize = self._serialize
        if self._parse_value:
            graphql_type.parse_value = self._parse_value
        if self._parse_literal:
            graphql_type.parse_literal = self._parse_literal
