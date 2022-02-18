from graphql import (
    GraphQLSchema,
    assert_valid_schema,
    build_ast_schema,
    parse,
)

from .deferred_type import DeferredType


def make_executable_schema(*types):
    flat_types_list = []
    find_requirements(flat_types_list, types)

    deferred_names = [
        deferred._graphql_name
        for deferred in filter(
            lambda obj: isinstance(obj, DeferredType), flat_types_list
        )
    ]

    real_types = [
        type_
        for type_ in filter(
            lambda obj: not isinstance(obj, DeferredType), flat_types_list
        )
    ]

    real_names = [type_._graphql_name for type_ in real_types]
    missing_names = set(deferred_names) - set(real_names)
    if missing_names:
        raise ValueError(
            "Following types are defined as deferred and are missing "
            f"from schema: {', '.join(missing_names)}"
        )

    sdl_bits = [type_.__schema__ for type_ in real_types]
    ast_document = parse("\n".join(sdl_bits))
    schema = build_ast_schema(ast_document)

    for type_ in real_types:
        type_.__bind_to_schema__(schema)

    assert_valid_schema(schema)

    return schema


def find_requirements(types_list, types):
    for type_ in types:
        if type_ not in types_list:
            types_list.append(type_)

        find_requirements(types_list, type_.__requires__)
