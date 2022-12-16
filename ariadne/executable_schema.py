from typing import Callable, Dict, List, Optional, Type, Union

from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    parse,
)

from .enums import (
    EnumType,
    set_default_enum_values_on_schema,
    validate_schema_enum_values,
)
from .resolvers import resolve_to
from .schema_visitor import SchemaDirectiveVisitor
from .types import SchemaBindable
from .utils import convert_camel_case_to_snake


ConvertNameCaseCallable = Callable[
    [str, Type[Union[GraphQLArgument, GraphQLField, GraphQLInputField]]], str
]
ConvertNameCase = Union[bool, ConvertNameCaseCallable]


def make_executable_schema(
    type_defs: Union[str, List[str]],
    *bindables: Union[SchemaBindable, List[SchemaBindable]],
    directives: Optional[Dict[str, Type[SchemaDirectiveVisitor]]] = None,
    convert_names_case: ConvertNameCase = False,
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

    if convert_names_case:
        convert_names_in_schema(
            schema,
            convert_names_case if callable(convert_names_case) else None,
        )

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


GRAPHQL_SPEC_TYPES = (
    "__Directive",
    "__EnumValue",
    "__Field",
    "__InputValue",
    "__Schema",
    "__Type",
)


def convert_names_in_schema(
    schema: GraphQLSchema,
    strategy: Optional[ConvertNameCaseCallable],
) -> None:
    strategy = strategy or default_convert_name_case_strategy

    for type_name, graphql_type in schema.type_map.items():
        if (
            isinstance(graphql_type, GraphQLObjectType)
            and type_name not in GRAPHQL_SPEC_TYPES
        ):
            convert_names_in_schema_object(graphql_type, strategy)
        if isinstance(graphql_type, GraphQLInputObjectType):
            convert_names_in_schema_input(graphql_type, strategy)


def convert_names_in_schema_object(
    graphql_type: GraphQLObjectType,
    strategy: ConvertNameCaseCallable,
) -> None:
    for field_name, field in graphql_type.fields.items():
        if field.args:
            convert_names_in_schema_args(field, strategy)

        if field.resolve or field_name.lower() == field_name:
            continue

        field.resolve = resolve_to(strategy(field_name, GraphQLField))


def convert_names_in_schema_args(
    graphql_type: GraphQLField,
    strategy: ConvertNameCaseCallable,
) -> None:
    for arg_name, arg in graphql_type.args.items():
        if arg.out_name or arg_name.lower() == arg_name:
            continue

        arg.out_name = strategy(arg_name, GraphQLInputField)


def convert_names_in_schema_input(
    graphql_type: GraphQLInputObjectType,
    strategy: ConvertNameCaseCallable,
) -> None:
    for field_name, field in graphql_type.fields.items():
        if field.out_name or field_name.lower() == field_name:
            continue

        field.out_name = strategy(field_name, GraphQLInputField)


def default_convert_name_case_strategy(graphql_name: str, _) -> str:
    return convert_camel_case_to_snake(graphql_name)
