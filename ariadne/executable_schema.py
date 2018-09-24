from typing import List, Union

from graphql import GraphQLSchema

from .build_schema import build_schema_from_type_definitions
from .resolvers import add_resolve_functions_to_schema


def flatten_map(resolver_map: dict) -> List[tuple]:
    for key, value in resolver_map.items():
        for resolver_name, resolver in value.items():
            yield (key, resolver_name, resolver)


def decompose_maps(resolver_maps: List[dict]) -> List[tuple]:
    for r_map in resolver_maps:
        for item in flatten_map(r_map):
            yield item


def merge_resolvers(resolver_list: List[tuple]) -> dict:
    output = {}
    for key, resolver_name, resolver in resolver_list:
        if key in output.keys():
            output[key].update({resolver_name: resolver})
        else:
            output[key] = {resolver_name: resolver}
    return output


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: Union[dict, List[dict]]
) -> GraphQLSchema:
    schema = build_schema_from_type_definitions(type_defs)
    if isinstance(resolvers, list):
        add_resolve_functions_to_schema(
            schema, merge_resolvers(decompose_maps(resolvers))
        )
    elif isinstance(resolvers, dict):
        add_resolve_functions_to_schema(schema, resolvers)
    return schema
