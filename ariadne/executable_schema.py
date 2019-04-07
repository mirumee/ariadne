from typing import List, Union

from graphql import GraphQLSchema, DocumentNode, parse, build_ast_schema, extend_schema

from .types import SchemaBindable


newExtensionDefinitionKind = 'object_type_extension'
interfaceExtensionDefinitionKind = 'interface_type_extension'
inputObjectExtensionDefinitionKind = 'input_object_type_extension'
unionExtensionDefinitionKind = 'union_type_extension'
enumExtensionDefinitionKind = 'enum_type_extension'

extension_kinds = [
    newExtensionDefinitionKind,
    interfaceExtensionDefinitionKind,
    inputObjectExtensionDefinitionKind,
    unionExtensionDefinitionKind,
    enumExtensionDefinitionKind,
]


def extract_extensions(ast: DocumentNode) -> DocumentNode:
    extensions = [node for node in ast.definitions if node.kind in extension_kinds]

    return DocumentNode(definitions=extensions)


def make_executable_schema(
    type_defs: Union[str, List[str]],
    bindables: Union[SchemaBindable, List[SchemaBindable], None] = None,
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    ast_document = parse(type_defs)

    schema = build_ast_schema(ast_document)

    extension_ast = extract_extensions(ast_document)

    if len(extension_ast.definitions):
        schema = extend_schema(schema, extension_ast)

    if isinstance(bindables, list):
        for obj in bindables:
            obj.bind_to_schema(schema)
    elif bindables:
        bindables.bind_to_schema(schema)

    return schema


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)
