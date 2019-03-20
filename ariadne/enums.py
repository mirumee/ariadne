import enum

from typing import Any, Dict, Union

from graphql.type import GraphQLEnumType, GraphQLSchema

from .types import Bindable


class EnumType(Bindable):
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

        for key, value in self.values.items():
            if key not in graphql_type.values:
                raise ValueError(
                    "Value %s is not defined on enum %s" % (key, self.name)
                )
            graphql_type.values[key].value = value

    def validate_graphql_type(self, graphql_type: str) -> None:
        if not graphql_type:
            raise ValueError("Enum %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLEnumType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLEnumType.__name__)
            )
