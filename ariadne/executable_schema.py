from typing import Dict, Generator, List, Tuple, Type, Union, Optional, cast

from graphql import (
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    parse,
)
from graphql.language.ast import (
    EnumValueNode,
    InputValueDefinitionNode,
    ObjectValueNode,
)
from graphql.pyutils.undefined import Undefined
from graphql.type.definition import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLObjectType,
)

from .enums import set_default_enum_values_on_schema
from .schema_visitor import SchemaDirectiveVisitor
from .types import SchemaBindable

ArgumentWithKeys = Tuple[str, str, GraphQLArgument, Optional[List["str"]]]
InputFieldWithKeys = Tuple[str, str, GraphQLInputField, Optional[List["str"]]]


def make_executable_schema(
    type_defs: Union[str, List[str]],
    *bindables: Union[SchemaBindable, List[SchemaBindable]],
    directives: Dict[str, Type[SchemaDirectiveVisitor]] = None,
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    ast_document = parse(type_defs)
    schema = build_ast_schema(ast_document)

    for bindable in bindables:
        if isinstance(bindable, list):
            for obj in bindable:
                obj.bind_to_schema(schema)
        else:
            bindable.bind_to_schema(schema)

    set_default_enum_values_on_schema(schema)

    if directives:
        SchemaDirectiveVisitor.visit_schema_directives(schema, directives)

    assert_valid_schema(schema)

    for type_name, field_name, arg, _ in find_enum_values_in_schema(schema):
        if is_invalid_enum_value(arg):
            raise ValueError(
                f"Value for type: <{arg.type}> is invalid. "
                f"Check InputField/Arguments for <{field_name}> in <{type_name}> "
                "(Undefined enum value)."
            )

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


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
