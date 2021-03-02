import enum

from typing import Any, Dict, Optional, Union, cast

from graphql.type import (
    GraphQLEnumType,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLArgument,
    GraphQLSchema,
)
from graphql.pyutils import Undefined

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
        self.bind_to_graphql_type(schema)
        self.bind_to_default_values(schema)

    def bind_to_graphql_type(self, schema: GraphQLSchema) -> None:
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

    def bind_to_default_values(self, schema: GraphQLSchema) -> None:
        for graphql_type in schema.type_map.values():
            if isinstance(graphql_type, GraphQLInputObjectType):
                for field_name, field in graphql_type.fields.items():
                    self.bind_to_input_field_default_value(
                        graphql_type, field_name, field
                    )

            if isinstance(graphql_type, GraphQLObjectType):
                for field_name, field in graphql_type.fields.items():
                    for arg_name, arg in field.args.items():
                        self.bind_to_arg_default_value(
                            graphql_type, field_name, arg_name, arg
                        )

    def bind_to_input_field_default_value(
        self,
        graphql_type: GraphQLInputObjectType,
        field_name: str,
        field: GraphQLInputField,
    ) -> None:
        if (
            isinstance(field.type, GraphQLEnumType)
            and field.type.name == self.name
            and field.default_value is not Undefined
        ):
            if field.default_value not in self.values:
                raise ValueError(
                    "Value %s is not defined on enum %s at field %s belonging to type %s"
                    % (
                        field.default_value,
                        self.name,
                        field_name,
                        graphql_type.name,
                    )
                )

            field.default_value = self.values[field.default_value]

    def bind_to_arg_default_value(
        self,
        graphql_type: GraphQLObjectType,
        field_name: str,
        arg_name: str,
        arg: Union[GraphQLArgument, GraphQLInputObjectType],
    ) -> None:
        if isinstance(arg.type, GraphQLInputObjectType) and arg.default_value:
            for arg_field_name, arg_field in arg.type.fields.items():
                default_value = arg.default_value.get(arg_field_name)
                if (
                    isinstance(arg_field.type, GraphQLEnumType)
                    and arg_field.type.name == self.name
                    and default_value is not None
                ):
                    if default_value not in self.values:
                        raise ValueError(
                            "Value %s is not defined on enum %s at arg %s on field %s belonging to type %s"
                            % (
                                arg.default_value,
                                self.name,
                                arg_name,
                                field_name,
                                graphql_type.name,
                            )
                        )

                    arg.default_value[arg_field_name] = self.values[default_value]

        if (
            isinstance(arg.type, GraphQLEnumType)
            and arg.type.name == self.name
            and arg.default_value is not None
        ):
            if arg.default_value not in self.values:
                raise ValueError(
                    "Value %s is not defined on enum %s at arg %s on field %s belonging to type %s"
                    % (
                        arg.default_value,
                        self.name,
                        arg_name,
                        field_name,
                        graphql_type.name,
                    )
                )

            arg.default_value = self.values[arg.default_value]


def set_default_enum_values_on_schema(schema: GraphQLSchema):
    for type_object in schema.type_map.values():
        if isinstance(type_object, GraphQLEnumType):
            set_default_enum_values(type_object)


def set_default_enum_values(graphql_type: GraphQLEnumType):
    for key in graphql_type.values:
        if graphql_type.values[key].value is None:
            graphql_type.values[key].value = key
