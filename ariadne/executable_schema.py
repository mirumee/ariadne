from typing import Dict, List, Type, Union

from graphql import (
    DocumentNode,
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    extend_schema,
    parse,
    validate_schema,
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
    schema = build_and_extend_schema(ast_document)
    validate_schema(schema)

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

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def build_and_extend_schema(ast: DocumentNode) -> GraphQLSchema:
    schema = build_ast_schema(ast)
    extension_ast = extract_extensions(ast)

    if extension_ast.definitions:
        schema = extend_schema(schema, extension_ast)

    return schema


EXTENSION_KINDS = [
    "scalar_type_extension",
    "object_type_extension",
    "interface_type_extension",
    "union_type_extension",
    "enum_type_extension",
    "input_object_type_extension",
]


def extract_extensions(ast: DocumentNode) -> DocumentNode:
    extensions = [node for node in ast.definitions if node.kind in EXTENSION_KINDS]
    return DocumentNode(definitions=extensions)
