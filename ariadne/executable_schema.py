from typing import Dict, List, NoReturn, Tuple, Type, Union, Optional

from graphql import (
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    parse,
)
from graphql.pyutils.undefined import Undefined
from graphql.type.definition import (
    GraphQLEnumType,
    GraphQLInputField,
    GraphQLInputObjectType,
)

from .enums import set_default_enum_values_on_schema
from .schema_visitor import SchemaDirectiveVisitor
from .types import SchemaBindable


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
    validate_default_enums(schema)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def validate_default_enums(schema: GraphQLSchema) -> Optional[NoReturn]:
    input_types = (
        input_
        for input_ in schema.type_map.values()
        if isinstance(input_, GraphQLInputObjectType)
    )

    for input_ in input_types:
        has_invalid, field_name = has_invalid_enum_field_input(input_)
        if has_invalid:
            raise ValueError(
                f"Value for type: <{input_.name}> at field: <{field_name}> is invalid "
                "(undefined enum value)."
            )


def has_invalid_enum_field_input(
    type_: GraphQLInputObjectType,
) -> Tuple[bool, Optional[GraphQLInputField]]:
    for name, field in type_.fields.items():
        if isinstance(field.type, (GraphQLEnumType, GraphQLInputObjectType)):
            is_field_invalid = is_invalid_enum_value(field)
            if is_field_invalid:
                return is_field_invalid, name

    return False, None


def is_invalid_enum_value(field: GraphQLInputField) -> bool:
    return field.default_value is Undefined and field.ast_node.default_value is not None
