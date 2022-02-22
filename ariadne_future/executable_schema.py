from typing import List

from graphql import (
    DocumentNode,
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    concat_ast,
    parse,
    print_schema,
)
from graphql.language import ast

from .deferred_type import DeferredType


ROOT_TYPES = ["Query", "Mutation", "Subscription"]


def make_executable_schema(
    *types,
    merge_roots: bool = True,
):
    all_types = []
    find_requirements(all_types, types)

    real_types = [
        type_
        for type_ in filter(lambda obj: not isinstance(obj, DeferredType), all_types)
    ]

    validate_no_missing_types(real_types, all_types)

    schema = build_schema(real_types, merge_roots)

    assert_valid_schema(schema)

    return schema


def find_requirements(types_list, types):
    for type_ in types:
        if type_ not in types_list:
            types_list.append(type_)

        find_requirements(types_list, type_.__requires__)


def validate_no_missing_types(real_types, all_types):
    deferred_names = [
        deferred._graphql_name
        for deferred in filter(lambda obj: isinstance(obj, DeferredType), all_types)
    ]

    real_names = [type_._graphql_name for type_ in real_types]
    missing_names = set(deferred_names) - set(real_names)
    if missing_names:
        raise ValueError(
            "Following types are defined as deferred and are missing "
            f"from schema: {', '.join(missing_names)}"
        )


def build_schema(types_list, merge_roots: bool = True) -> GraphQLSchema:
    schema_definitions: List[ast.DocumentNode] = []
    if merge_roots:
        schema_definitions.append(build_root_schema(types_list))
        for type_ in types_list:
            if type_._graphql_name not in ROOT_TYPES or not merge_roots:
                schema_definitions.append(parse(type_.__schema__))

    ast_document = concat_ast(schema_definitions)
    schema = build_ast_schema(ast_document)

    for type_ in types_list:
        type_.__bind_to_schema__(schema)

    return schema


def build_root_schema(types_list) -> DocumentNode:
    root_types = {
        "Query": [],
        "Mutation": [],
        "Subscription": [],
    }

    for type_ in types_list:
        if type_._graphql_name in root_types:
            root_types[type_._graphql_name].append(type_)

    schema = []
    for types_defs in root_types.values():
        if len(types_defs) == 1:
            schema.append(parse(types_defs[0].__schema__))
        elif types_defs:
            schema.append(merge_root_types(types_defs))

    return concat_ast(schema)


def merge_root_types(types_list) -> DocumentNode:
    interfaces = []
    directives = []
    fields = {}

    for type_ in types_list:
        type_definition = parse(type_.__schema__).definitions[0]
        interfaces.extend(type_definition.interfaces)
        directives.extend(type_definition.directives)

        for field_def in type_definition.fields:
            field_name = field_def.name.value
            if field_name in fields:
                other_type_name = fields[field_name][1].__name__
                raise ValueError(
                    f"Multiple {type_._graphql_name} types are defining same field "
                    f"'{field_name}': {other_type_name}, {type_.__name__}"
                )

            fields[field_name] = (field_def, type_)

    merged_definition = ast.ObjectTypeDefinitionNode()
    merged_definition.name = ast.NameNode()
    merged_definition.name.value = types_list[0]._graphql_name
    merged_definition.interfaces = tuple(interfaces)
    merged_definition.directives = tuple(directives)
    merged_definition.fields = tuple(
        fields[field_name][0] for field_name in sorted(fields)
    )

    merged_document = DocumentNode()
    merged_document.definitions = (merged_definition,)

    return merged_document
