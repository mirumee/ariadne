from collections import defaultdict
from itertools import chain
from typing import List, Union

from graphql import GraphQLSchema

from .build_schema import build_schema_from_type_definitions
from .resolvers import add_resolve_functions_to_schema


def concatenate_type_defs(type_defs: List[str]) -> str:
    resolved_type_defs = []
    for type_def in type_defs:
        resolved_type_defs.append(type_def.strip())
    return "\n\n".join(resolved_type_defs)


def decompose_maps(resolvers_map):
    def flatten(rm):
        for key, value in rm.items():
            for resolver_name, resolver in value.items():
                yield (key, resolver_name, resolver)

    return chain.from_iterable(flatten(m) for m in resolvers_map)


def merge_resolvers(resolver_list):
    output = defaultdict(dict)
    for key, resolver_name, resolver in resolver_list:
        output[key][resolver_name] = resolver
    return output


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: Union[dict, List[dict]]
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = concatenate_type_defs(type_defs)

    schema = build_schema_from_type_definitions(type_defs)

    if isinstance(resolvers, list):
        add_resolve_functions_to_schema(
            schema, merge_resolvers(decompose_maps(resolvers))
        )
    elif isinstance(resolvers, dict):
        add_resolve_functions_to_schema(schema, resolvers)
    return schema
