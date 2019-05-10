import enum

from typing import Any, Dict, Optional, Union, cast

from graphql.type import GraphQLEnumType, GraphQLNamedType, GraphQLSchema

from .types import SchemaBindable


class EnumType(SchemaBindable):
    def __init__(
        self, name: str, values=Union[Dict[str, Any], enum.Enum, enum.IntEnum]
    ) -> None:
        self.name = name
        try:
            self.values = values.__members__  # pylint: disable=no-member
        except AttributeError:
            self.values = values

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLEnumType, graphql_type)

        for key, value in self.values.items():
            if key not in graphql_type.values:
                raise ValueError(
                    "Value %s is not defined on enum %s" % (key, self.name)
                )
            graphql_type.values[key].value = value

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        if not graphql_type:
            raise ValueError("Enum %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLEnumType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLEnumType.__name__)
            )


def set_default_enum_values_on_schema(schema: GraphQLSchema):
    for type_object in schema.type_map.values():
        if isinstance(type_object, GraphQLEnumType):
            set_default_enum_values(type_object)


def set_default_enum_values(graphql_type: GraphQLEnumType):
    for key in graphql_type.values:
        if graphql_type.values[key].value is None:
            graphql_type.values[key].value = key
