from typing import Dict, List, Optional, Type, Union

from graphql import (
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
from .schema_names import SchemaNameConverter, convert_schema_names
from .schema_visitor import SchemaDirectiveVisitor
from .types import SchemaBindable


def make_executable_schema(
    type_defs: Union[str, List[str]],
    *bindables: Union[SchemaBindable, List[SchemaBindable]],
    directives: Optional[Dict[str, Type[SchemaDirectiveVisitor]]] = None,
    convert_names_case: Union[bool, SchemaNameConverter] = False,
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
        convert_schema_names(
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
