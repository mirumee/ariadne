from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union, cast

from graphql import (
    EnumValueNode,
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLType,
    InputValueDefinitionNode,
    ListValueNode,
    ObjectValueNode,
)


class GraphQLEnumsValuesVisitor:
    schema: GraphQLSchema
    enum_values: dict[str, dict[str, Any]]

    def __init__(self, schema: GraphQLSchema):
        self.enum_values = {}
        self.schema = schema

        self.visit_enum_types()
        self.visit_schema()

    def visit_enum_types(self) -> None:
        for type_def in self.schema.type_map.values():
            if isinstance(type_def, GraphQLEnumType):
                self.enum_values[type_def.name] = {
                    key: value.value for key, value in type_def.values.items()
                }

    def visit_schema(self) -> None:
        raise NotImplementedError(
            "GraphQLEnumsValuesVisitor subclasses must implement 'visit_schema'"
        )


class GraphQLSchemaEnumsValuesVisitor(GraphQLEnumsValuesVisitor):
    def visit_schema(self) -> None:
        for type_def in self.schema.type_map.values():
            if type_def.name.startswith("__"):
                continue  # Skip introspection types

            if isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType)):
                self.visit_object(type_def)

            if isinstance(type_def, GraphQLInputObjectType):
                self.visit_input(type_def)

    def visit_object(
        self,
        object_def: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> None:
        for field_name, field_def in object_def.fields.items():
            for arg_name, arg_def in field_def.args.items():
                self.visit_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                )

    def visit_input(
        self,
        input_def: GraphQLInputObjectType,
    ) -> None:
        for field_name, field_def in input_def.fields.items():
            self.visit_value(input_def, field_name, field_def)

    def visit_value(
        self,
        object_def: Union[
            GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType
        ],
        field_name: str,
        field_def: Union[GraphQLField, GraphQLInputField],
        arg_name: Optional[str] = None,
        arg_def: Optional[GraphQLArgument] = None,
    ) -> None:
        src_def: Union[GraphQLInputField, GraphQLArgument]
        if isinstance(field_def, GraphQLInputField):
            src_def = field_def
        elif isinstance(arg_def, GraphQLArgument):
            src_def = arg_def

        if src_def.default_value:
            if is_graphql_list(src_def.type) and isinstance(
                src_def.default_value, list
            ):
                self.visit_list_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    src_def.type,
                    src_def.default_value,
                )

            else:
                src_type = unwrap_type(src_def.type)
                if isinstance(src_type, GraphQLEnumType) and is_raw_enum_value(
                    src_def.default_value
                ):
                    self.visit_schema_enum_default_value(
                        GraphQLSchemaEnumDefaultValueLocation(
                            enum_name=src_type.name,
                            enum_value=src_def.default_value,
                            object_name=object_def.name,
                            object_def=object_def,
                            field_name=field_name,
                            field_def=field_def,
                            arg_name=arg_name,
                            arg_def=arg_def,
                            default_value=src_def.default_value,
                            default_value_path=None,
                        )
                    )

                elif isinstance(src_type, GraphQLInputObjectType):
                    self.visit_input_value(
                        object_def,
                        field_name,
                        field_def,
                        arg_name,
                        arg_def,
                        src_type,
                        src_def.default_value,
                    )

    def visit_list_value(
        self,
        object_def: Union[
            GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType
        ],
        field_name: str,
        field_def: Union[GraphQLField, GraphQLInputField],
        arg_name: Optional[str],
        arg_def: Optional[GraphQLArgument],
        value_def: GraphQLType,
        value: Any,
    ) -> None:
        value_type = unwrap_list_type(value_def)
        if is_graphql_list(value_type):
            for value_item in value:
                self.visit_list_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    value_type,
                    value_item,
                )

        elif isinstance(value_type, GraphQLEnumType):
            for default_value_path, enum_value in enumerate(value):
                if is_raw_enum_value(enum_value):
                    self.visit_schema_enum_default_value(
                        GraphQLSchemaEnumDefaultValueLocation(
                            enum_name=value_type.name,
                            enum_value=enum_value,
                            object_name=object_def.name,
                            object_def=object_def,
                            field_name=field_name,
                            field_def=field_def,
                            arg_name=arg_name,
                            arg_def=arg_def,
                            default_value=value,
                            default_value_path=default_value_path,
                        )
                    )

        elif isinstance(value_type, GraphQLInputObjectType):
            for value_item in value:
                if isinstance(value_item, dict):
                    self.visit_input_value(
                        object_def,
                        field_name,
                        field_def,
                        arg_name,
                        arg_def,
                        value_type,
                        value_item,
                    )

    def visit_input_value(
        self,
        object_def: Union[
            GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType
        ],
        field_name: str,
        field_def: Union[GraphQLField, GraphQLInputField],
        arg_name: Optional[str],
        arg_def: Optional[GraphQLArgument],
        value_def: GraphQLInputObjectType,
        value: dict,
    ) -> None:
        for input_field_name, input_field_def in value_def.fields.items():
            input_field_value = value.get(input_field_name)
            if input_field_value is None:
                continue  # Skip field

            input_field_type = unwrap_type(input_field_def.type)
            if is_graphql_list(input_field_def.type) and isinstance(
                input_field_value, list
            ):
                self.visit_list_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    input_field_def.type,
                    input_field_value,
                )

            elif isinstance(input_field_type, GraphQLEnumType) and is_raw_enum_value(
                input_field_value
            ):
                self.visit_schema_enum_default_value(
                    GraphQLSchemaEnumDefaultValueLocation(
                        enum_name=input_field_type.name,
                        enum_value=input_field_value,
                        object_name=object_def.name,
                        object_def=object_def,
                        field_name=field_name,
                        field_def=field_def,
                        arg_name=arg_name,
                        arg_def=arg_def,
                        default_value=value,
                        default_value_path=input_field_name,
                    )
                )

            elif isinstance(input_field_type, GraphQLInputObjectType) and isinstance(
                input_field_value, dict
            ):
                self.visit_input_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    input_field_type,
                    input_field_value,
                )

    def visit_schema_enum_default_value(
        self, location: "GraphQLSchemaEnumDefaultValueLocation"
    ) -> None:
        pass


@dataclass(frozen=True)
class GraphQLSchemaEnumDefaultValueLocation:
    enum_name: str
    enum_value: Any
    object_name: str
    object_def: Union[GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType]
    field_name: str
    field_def: Union[GraphQLField, GraphQLInputField]
    arg_name: Optional[str] = None
    arg_def: Optional[GraphQLArgument] = None
    default_value: Any = None
    default_value_path: Any = None


class GraphQLASTEnumsValuesVisitor(GraphQLEnumsValuesVisitor):
    def visit_schema(self) -> None:
        for type_def in self.schema.type_map.values():
            if type_def.name.startswith("__"):
                continue  # Skip introspection types

            if (
                isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType))
                and type_def.ast_node
            ):
                self.visit_object(type_def)

            if isinstance(type_def, GraphQLInputObjectType) and type_def.ast_node:
                self.visit_input(type_def)

    def visit_object(
        self,
        object_def: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> None:
        for field_name, field_def in object_def.fields.items():
            for arg_name, arg_def in field_def.args.items():
                if arg_def.ast_node and arg_def.ast_node.default_value:
                    self.visit_value(
                        object_def,
                        field_name,
                        field_def,
                        arg_name,
                        arg_def,
                    )

    def visit_input(
        self,
        input_def: GraphQLInputObjectType,
    ) -> None:
        for field_name, field_def in input_def.fields.items():
            if field_def.ast_node and field_def.ast_node.default_value:
                self.visit_value(
                    input_def,
                    field_name,
                    field_def,
                )

    def visit_value(
        self,
        object_def: Union[
            GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType
        ],
        field_name: str,
        field_def: Union[GraphQLField, GraphQLInputField],
        arg_name: Optional[str] = None,
        arg_def: Optional[GraphQLArgument] = None,
    ) -> None:
        src_def: Union[GraphQLInputField, GraphQLArgument]
        if isinstance(field_def, GraphQLInputField):
            src_def = field_def
        elif isinstance(arg_def, GraphQLArgument):
            src_def = arg_def

        ast_node = cast(InputValueDefinitionNode, src_def.ast_node)
        default_value_ast = ast_node.default_value
        if is_graphql_list(src_def.type) and isinstance(
            default_value_ast, ListValueNode
        ):
            self.visit_list_value(
                object_def,
                field_name,
                field_def,
                arg_name,
                arg_def,
                src_def.type,
                default_value_ast,
            )

        else:
            src_type = unwrap_type(src_def.type)
            if isinstance(src_type, GraphQLEnumType) and isinstance(
                default_value_ast, EnumValueNode
            ):
                self.visit_ast_enum_default_value(
                    GraphQLASTEnumDefaultValueLocation(
                        enum_name=src_type.name,
                        enum_value=default_value_ast.value,
                        object_name=object_def.name,
                        object_def=object_def,
                        field_name=field_name,
                        field_def=field_def,
                        arg_name=arg_name,
                        arg_def=arg_def,
                        ast_node=default_value_ast,
                        ast_node_path=None,
                    )
                )

            elif isinstance(src_type, GraphQLInputObjectType) and isinstance(
                default_value_ast, ObjectValueNode
            ):
                self.visit_input_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    src_type,
                    default_value_ast,
                )

    def visit_list_value(
        self,
        object_def: Union[
            GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType
        ],
        field_name: str,
        field_def: Union[GraphQLField, GraphQLInputField],
        arg_name: Optional[str],
        arg_def: Optional[GraphQLArgument],
        value_def: GraphQLType,
        value_ast: ListValueNode,
    ) -> None:
        value_type = unwrap_list_type(value_def)
        if is_graphql_list(value_type):
            for value_item in value_ast.values:
                self.visit_list_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    value_type,
                    cast(ListValueNode, value_item),
                )

        elif isinstance(value_type, GraphQLEnumType):
            for default_value_path, enum_value in enumerate(value_ast.values):
                if isinstance(enum_value, EnumValueNode):
                    self.visit_ast_enum_default_value(
                        GraphQLASTEnumDefaultValueLocation(
                            enum_name=value_type.name,
                            enum_value=enum_value.value,
                            object_name=object_def.name,
                            object_def=object_def,
                            field_name=field_name,
                            field_def=field_def,
                            arg_name=arg_name,
                            arg_def=arg_def,
                            ast_node=value_ast,
                            ast_node_path=default_value_path,
                        )
                    )

        elif isinstance(value_type, GraphQLInputObjectType):
            for value_item in value_ast.values:
                if isinstance(value_item, ObjectValueNode):
                    self.visit_input_value(
                        object_def,
                        field_name,
                        field_def,
                        arg_name,
                        arg_def,
                        value_type,
                        value_item,
                    )

    def visit_input_value(
        self,
        object_def: Union[
            GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType
        ],
        field_name: str,
        field_def: Union[GraphQLField, GraphQLInputField],
        arg_name: Optional[str],
        arg_def: Optional[GraphQLArgument],
        value_def: GraphQLInputObjectType,
        value_ast: ObjectValueNode,
    ) -> None:
        value: dict[str, Any] = {
            field.name.value: field.value for field in value_ast.fields
        }

        for input_field_name, input_field_def in value_def.fields.items():
            input_field_value = value.get(input_field_name)
            if input_field_value is None:
                continue  # Skip field

            input_field_type = unwrap_type(input_field_def.type)
            if is_graphql_list(input_field_def.type) and isinstance(
                input_field_value, ListValueNode
            ):
                self.visit_list_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    input_field_def.type,
                    input_field_value,
                )

            elif isinstance(input_field_type, GraphQLEnumType) and isinstance(
                input_field_value, EnumValueNode
            ):
                self.visit_ast_enum_default_value(
                    GraphQLASTEnumDefaultValueLocation(
                        enum_name=input_field_type.name,
                        enum_value=input_field_value.value,
                        object_name=object_def.name,
                        object_def=object_def,
                        field_name=field_name,
                        field_def=field_def,
                        arg_name=arg_name,
                        arg_def=arg_def,
                        ast_node=value,
                        ast_node_path=input_field_name,
                    )
                )

            elif isinstance(input_field_type, GraphQLInputObjectType) and isinstance(
                input_field_value, ObjectValueNode
            ):
                self.visit_input_value(
                    object_def,
                    field_name,
                    field_def,
                    arg_name,
                    arg_def,
                    input_field_type,
                    input_field_value,
                )

    def visit_ast_enum_default_value(
        self, location: "GraphQLASTEnumDefaultValueLocation"
    ) -> None:
        pass


@dataclass(frozen=True)
class GraphQLASTEnumDefaultValueLocation:
    enum_name: str
    enum_value: Any
    object_name: str
    object_def: Union[GraphQLInputObjectType, GraphQLInterfaceType, GraphQLObjectType]
    field_name: str
    field_def: Union[GraphQLField, GraphQLInputField]
    arg_name: Optional[str] = None
    arg_def: Optional[GraphQLArgument] = None
    ast_node: Any = None
    ast_node_path: Any = None


def unwrap_type(graphql_type: GraphQLType) -> GraphQLType:
    if isinstance(graphql_type, (GraphQLList, GraphQLNonNull)):
        return unwrap_type(graphql_type.of_type)

    return graphql_type


def unwrap_list_type(graphql_type: GraphQLType) -> GraphQLType:
    if isinstance(graphql_type, GraphQLNonNull):
        return unwrap_list_type(graphql_type.of_type)

    if isinstance(graphql_type, GraphQLList):
        return unwrap_nonnull_type(graphql_type.of_type)

    return graphql_type


def unwrap_nonnull_type(graphql_type: GraphQLType) -> GraphQLType:
    if isinstance(graphql_type, GraphQLNonNull):
        return unwrap_nonnull_type(graphql_type.of_type)

    return graphql_type


def is_graphql_list(graphql_type: GraphQLType) -> bool:
    if isinstance(graphql_type, GraphQLNonNull):
        return is_graphql_list(graphql_type.of_type)

    return isinstance(graphql_type, GraphQLList)


def is_raw_enum_value(value: Any) -> bool:
    # Raw enum value is a str with key name
    return isinstance(value, str) and not isinstance(value, Enum)
