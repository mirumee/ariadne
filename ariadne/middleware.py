from typing import Callable

from graphql import GraphQLResolveInfo

from .utils import convert_kwargs_to_snake_case


def convert_kwargs_to_snake_case_middleware(resolver: Callable, *args, **kwargs):
    """Convert all kwargs to snake case."""
    info: GraphQLResolveInfo = args[1]
    is_introspection_query = "__schema" in info.path.as_list()

    # Introspection query resolvers use camelCase variables so if you would convert
    # those as well a TypeError would be raised.
    if is_introspection_query:
        return resolver(*args, **kwargs)
    return convert_kwargs_to_snake_case(resolver)(*args, **kwargs)
