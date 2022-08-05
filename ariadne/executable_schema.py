from typing import Dict, List, Type, Union

from graphql import (
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    parse,
)
from graphql.type import GraphQLObjectType, GraphQLInputObjectType

from .enums import (
    EnumType,
    set_default_enum_values_on_schema,
    validate_schema_enum_values,
)
from .schema_visitor import SchemaDirectiveVisitor
from .types import SchemaBindable
from .utils import convert_camel_case_to_snake


def make_executable_schema(
    type_defs: Union[str, List[str]],
    *bindables: Union[SchemaBindable, List[SchemaBindable]],
    directives: Dict[str, Type[SchemaDirectiveVisitor]] = None,
    convert_args_to_snake_case: bool = False,
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    ast_document = parse(type_defs)
    schema = build_ast_schema(ast_document)
    flat_bindables: List[SchemaBindable] = flatten_bindables(*bindables)

    for bindable in flat_bindables:
        bindable.bind_to_schema(schema)

    set_default_enum_values_on_schema(schema)

    if directives:
        SchemaDirectiveVisitor.visit_schema_directives(schema, directives)

    assert_valid_schema(schema)
    validate_schema_enum_values(schema)
    repair_default_enum_values(schema, flat_bindables)

    if convert_args_to_snake_case:
        set_outnames_to_snake_case(schema)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def flatten_bindables(
    *bindables: Union[SchemaBindable, List[SchemaBindable]]
) -> List[SchemaBindable]:
    new_bindables = []

    for bindable in bindables:
        if isinstance(bindable, list):
            new_bindables.extend(bindable)
        else:
            new_bindables.append(bindable)

    return new_bindables


def repair_default_enum_values(schema, bindables) -> None:
    for bindable in bindables:
        if isinstance(bindable, EnumType):
            bindable.bind_to_default_values(schema)


def set_outnames_to_snake_case(schema) -> None:
    for graphql_type in schema.type_map.values():
        if isinstance(graphql_type, GraphQLInputObjectType):
            for field_name, field in graphql_type.fields.items():
                field.out_name = convert_camel_case_to_snake(field_name)
        if isinstance(graphql_type, GraphQLObjectType):
            for field in graphql_type.fields.values():
                for arg_name, arg in field.args.items():
                    arg.out_name = convert_camel_case_to_snake(arg_name)
