import re
import os
from typing import Dict, List, Optional, Type, Union, cast

from graphql import extend_schema, parse
from graphql.language import DocumentNode
from graphql.language.ast import ObjectTypeDefinitionNode
from graphql.type import (
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLUnionType,
)

from ...executable_schema import (
    SchemaBindables,
    make_executable_schema,
    join_type_defs,
)
from ...schema_names import SchemaNameConverter
from ...schema_visitor import SchemaDirectiveVisitor
from ...load_schema import load_schema_from_path
from .utils import get_entity_types, purge_schema_directives, resolve_entities

base_federation_service_type_defs = """
    scalar _Any

    type _Service {{
        sdl: String
    }}

    {type_token} Query {{
        _service: _Service!
    }}
"""

federation_entity_type_defs = """
    union _Entity

    extend type Query {
        _entities(representations: [_Any!]!): [_Entity]!
    }
"""


def has_query_type(type_defs: str) -> bool:
    ast_document = parse(type_defs)
    return any(
        (
            isinstance(definition, ObjectTypeDefinitionNode)
            and definition.name.value == "Query"
        )
        for definition in ast_document.definitions
    )


def make_federated_schema(
    type_defs: Union[str, List[str]],
    *bindables: SchemaBindables,
    directives: Optional[Dict[str, Type[SchemaDirectiveVisitor]]] = None,
    convert_names_case: Union[bool, SchemaNameConverter] = False,
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    # Remove custom schema directives (to avoid apollo-gateway crashes).
    # NOTE: This does NOT interfere with ariadne's directives support.
    sdl = purge_schema_directives(type_defs)
    type_token = "extend type" if has_query_type(sdl) else "type"
    federation_service_type = base_federation_service_type_defs.format(
        type_token=type_token
    )

    tdl = [type_defs, federation_service_type]

    link = re.search(
        r"(?<=@link).*?url:.*?\"(.*?)\".?[^)]+?", sdl, re.MULTILINE | re.DOTALL
    )  # use regex to parse if it's fed 1 or fed 2; adds dedicated typedefs per spec
    dirname = os.path.dirname(__file__)
    if link and link.group(1) == "https://specs.apollo.dev/federation/v2.0":
        definitions = load_schema_from_path(
            os.path.join(dirname, "./definitions/fed2_0.graphql")
        )
    elif link and link.group(1) == "https://specs.apollo.dev/federation/v2.1":
        definitions = load_schema_from_path(
            os.path.join(dirname, "./definitions/fed2_1.graphql")
        )
    elif link and link.group(1) == "https://specs.apollo.dev/federation/v2.2":
        definitions = load_schema_from_path(
            os.path.join(dirname, "./definitions/fed2_2.graphql")
        )
    elif link and link.group(1) == "https://specs.apollo.dev/federation/v2.3":
        definitions = load_schema_from_path(
            os.path.join(dirname, "./definitions/fed2_3.graphql")
        )
    else:
        definitions = load_schema_from_path(
            os.path.join(dirname, "./definitions/fed1_0.graphql")
        )

    tdl.append(definitions)

    type_defs = join_type_defs(tdl)
    schema = make_executable_schema(
        type_defs,
        *bindables,
        directives=directives,
        convert_names_case=convert_names_case,
    )

    # Parse through the schema to find all entities with key directive.
    entity_types = get_entity_types(schema)
    has_entities = len(entity_types) > 0

    # Add the federation type definitions.
    if has_entities:
        schema = extend_federated_schema(schema, parse(federation_entity_type_defs))

        # Add _entities query.
        entity_type = schema.get_type("_Entity")
        if entity_type:
            entity_type = cast(GraphQLUnionType, entity_type)
            entity_type.types = entity_types

        query_type = schema.get_type("Query")
        if query_type:
            query_type = cast(GraphQLObjectType, query_type)
            query_type.fields["_entities"].resolve = resolve_entities

    # Add _service query.
    query_type = schema.get_type("Query")
    if query_type:
        query_type = cast(GraphQLObjectType, query_type)
        query_type.fields["_service"].resolve = lambda _service, info: {"sdl": sdl}

    return schema


def extend_federated_schema(
    schema: GraphQLSchema,
    document_ast: DocumentNode,
    assume_valid: bool = False,
    assume_valid_sdl: bool = False,
) -> GraphQLSchema:
    extended_schema = extend_schema(
        schema,
        document_ast,
        assume_valid,
        assume_valid_sdl,
    )

    for k, v in schema.type_map.items():
        resolve_reference = getattr(v, "__resolve_reference__", None)
        if resolve_reference and k in extended_schema.type_map:
            setattr(
                extended_schema.type_map[k],
                "__resolve_reference__",
                resolve_reference,
            )

    return extended_schema
