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


def build_schema_from_type_definitions(type_defs: str) -> GraphQLSchema:
    document = parse(type_defs)

    if not document_has_schema(document):
        schema_definition = build_default_schema(document)
        document.definitions.append(schema_definition)

    return build_ast_schema(document)


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
