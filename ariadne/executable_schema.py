from collections import defaultdict
from itertools import chain
from typing import Iterator, List, Union

from graphql import GraphQLSchema

from .build_schema import build_schema_from_type_definitions
from .resolvers import add_resolve_functions_to_schema


def decompose_maps(resolvers_maps: List[dict]) -> Iterator[tuple]:
    def flatten(rm):
        for key, value in rm.items():
            for resolver_name, resolver in value.items():
                yield (key, resolver_name, resolver)

    return chain.from_iterable(flatten(m) for m in resolvers_maps)


def merge_resolvers(resolver_list: Iterator[tuple]) -> dict:
    output = defaultdict(dict)  # type: dict
    for key, resolver_name, resolver in resolver_list:
        output[key][resolver_name] = resolver
    return output


def join_type_defs(type_defs: List[str]) -> str:
    return "\n\n".join(t.strip() for t in type_defs)


def make_executable_schema(
    type_defs: Union[str, List[str]], resolvers: Union[dict, List[dict]]
) -> GraphQLSchema:
    if isinstance(type_defs, list):
        type_defs = join_type_defs(type_defs)

    schema = build_schema_from_type_definitions(type_defs)

    if isinstance(resolvers, list):
        add_resolve_functions_to_schema(
            schema, merge_resolvers(decompose_maps(resolvers))
        )
    elif isinstance(resolvers, dict):
        add_resolve_functions_to_schema(schema, resolvers)

    return schema
