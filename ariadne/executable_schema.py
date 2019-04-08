from typing import List, Union

from graphql import GraphQLSchema, DocumentNode, parse, build_ast_schema, extend_schema

from .types import SchemaBindable


new_extension_definition_kind = "object_type_extension"
interface_extension_definition_kind = "interface_type_extension"
input_object_extension_definition_kind = "input_object_type_extension"
union_extension_definition_kind = "union_type_extension"
enum_extension_definition_kind = "enum_type_extension"

extension_kinds = [
    new_extension_definition_kind,
    interface_extension_definition_kind,
    input_object_extension_definition_kind,
    union_extension_definition_kind,
    enum_extension_definition_kind,
]


def extract_extensions(ast: DocumentNode) -> DocumentNode:
    extensions = [node for node in ast.definitions if node.kind in extension_kinds]

    return DocumentNode(definitions=extensions)


def build_and_extend_schema(ast: DocumentNode) -> GraphQLSchema:
    schema = build_ast_schema(ast)

    extension_ast = extract_extensions(ast)

    if extension_ast.definitions:
        schema = extend_schema(schema, extension_ast)

    return schema


def make_executable_schema(
    type_defs: Union[str, List[str]],
    bindables: Union[SchemaBindable, List[SchemaBindable], None] = None,
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    ast_document = parse(type_defs)

    schema = build_and_extend_schema(ast_document)

    if isinstance(bindables, list):
        for obj in bindables:
            obj.bind_to_schema(schema)
    elif bindables:
        bindables.bind_to_schema(schema)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)
