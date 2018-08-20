from typing import List, Union

from graphql import GraphQLSchema, parse
from graphql.language.ast import (
    Document,
    ObjectTypeDefinition,
    OperationTypeDefinition,
    Name,
    NamedType,
    SchemaDefinition,
)
from graphql.utils.build_ast_schema import build_ast_schema

TypeDef = Union[str, Document]
TypeDefs = Union[TypeDef, List[TypeDef]]


def build_default_schema(document: Document) -> SchemaDefinition:
    defined_types = [
        td.name.value
        for td in document.definitions
        if isinstance(td, ObjectTypeDefinition)
    ]
    operations = []
    if "Query" in defined_types:
        operations.append(
            OperationTypeDefinition("query", type=NamedType(name=Name("Query")))
        )
    if "Mutation" in defined_types:
        operations.append(
            OperationTypeDefinition("mutation", type=NamedType(name=Name("Mutation")))
        )
    if "Subscription" in defined_types:
        operations.append(
            OperationTypeDefinition(
                "subscription", type=NamedType(name=Name("Subscription"))
            )
        )
    return SchemaDefinition(operation_types=operations, directives=[])


def document_has_schema(document: Document) -> bool:
    return any(isinstance(td, SchemaDefinition) for td in document.definitions)


def concatenate_type_defs(type_defs: TypeDefs):
    resolved_type_defs = []
    for type_def in type_defs:
        if isinstance(type_def, str):
            resolved_type_defs.append(type_def)
        if isinstance(type_def, Document):
            resolved_type_defs.append(str(type_def))
    return '\n'.join(resolved_type_defs)


def build_schema_from_type_definitions(type_defs: TypeDefs) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = concatenate_type_defs(type_defs)

    document = parse(type_defs)
    if not document_has_schema(document):
        schema_definition = build_default_schema(document)
        document.definitions.append(schema_definition)
    return build_ast_schema(document)

