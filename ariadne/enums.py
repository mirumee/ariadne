import enum
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, cast

from graphql.type import GraphQLEnumType, GraphQLNamedType, GraphQLSchema
from graphql.language.ast import (
    EnumValueNode,
    InputValueDefinitionNode,
    ObjectValueNode,
)
from graphql.pyutils.undefined import Undefined
from graphql.type.definition import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLObjectType,
)

from .types import SchemaBindable


ArgumentWithKeys = Tuple[str, str, GraphQLArgument, Optional[List["str"]]]
InputFieldWithKeys = Tuple[str, str, GraphQLInputField, Optional[List["str"]]]


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


def find_enum_values_in_schema(
    schema: GraphQLSchema,
) -> Generator[Union[ArgumentWithKeys, InputFieldWithKeys], None, None]:
    object_types = (
        (name, object_)
        for name, object_ in schema.type_map.items()
        if isinstance(object_, GraphQLObjectType)
    )
    input_types = (
        (name, input_)
        for name, input_ in schema.type_map.items()
        if isinstance(input_, GraphQLInputObjectType)
    )
    for name, type_ in object_types:
        yield from enum_values_in_type_fields(name, type_)

    for name, input_ in input_types:
        yield from enum_values_in_input_fields(name, input_)


def enum_values_in_type_fields(
    field_name: str,
    type_: GraphQLObjectType,
) -> Generator[ArgumentWithKeys, None, None]:
    for field in type_.fields.values():
        yield from enum_values_in_field_args(field_name, field)


def enum_values_in_input_fields(
    field_name,
    input_: GraphQLInputObjectType,
) -> Generator[InputFieldWithKeys, None, None]:
    for input_name, field in input_.fields.items():
        if isinstance(field.type, GraphQLEnumType):
            yield field_name, input_name, field, None
        if isinstance(field.type, GraphQLInputObjectType):
            if field.ast_node is not None:
                routes = get_enum_keys_from_ast(field.ast_node)
                for route in routes:
                    yield field_name, input_name, field, route


def enum_values_in_field_args(
    field_name: str,
    field: GraphQLField,
) -> Generator[ArgumentWithKeys, None, None]:
    args = [
        (name, arg)
        for name, arg in field.args.items()
        if isinstance(arg.type, (GraphQLInputObjectType, GraphQLEnumType))
    ]
    for arg_name, arg in args:
        if isinstance(arg.type, GraphQLEnumType):
            yield field_name, arg_name, arg, None
        if isinstance(arg.type, GraphQLInputObjectType):
            if arg.ast_node is not None and arg.ast_node.default_value is not None:
                routes = get_enum_keys_from_ast(arg.ast_node)
                for route in routes:
                    yield field_name, arg_name, arg, route


def get_enum_keys_from_ast(ast_node: InputValueDefinitionNode) -> List[List["str"]]:
    routes = []
    object_node = ast_node.default_value
    object_node = cast(ObjectValueNode, object_node)
    nodes = [([field.name.value], field) for field in object_node.fields]

    while nodes:
        key_list, field = nodes.pop()
        if isinstance(field.value, EnumValueNode):
            routes.append(key_list)

        if isinstance(field.value, ObjectValueNode):
            for new_field in field.value.fields:
                new_route = key_list[:]
                new_route.append(new_field.name.value)
                nodes.append((new_route, new_field))

    return routes


def is_invalid_enum_value(field: Union[GraphQLInputField, GraphQLArgument]) -> bool:
    if field.ast_node is None:
        return False
    return field.default_value is Undefined and field.ast_node.default_value is not None


def validate_schema_enum_values(schema: GraphQLSchema) -> None:
    for type_name, field_name, arg, _ in find_enum_values_in_schema(schema):
        if is_invalid_enum_value(arg):
            raise ValueError(
                f"Value for type: <{arg.type}> is invalid. "
                f"Check InputField/Arguments for <{field_name}> in <{type_name}> "
                "(Undefined enum value)."
            )
