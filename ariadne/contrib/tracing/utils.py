from graphql import GraphQLResolveInfo, ResponsePath

from ...resolvers import is_default_resolver


def format_path(path: ResponsePath):
    elements = []
    while path:
        elements.append(path.key)
        path = path.prev
    return elements[::-1]


def should_trace(info: GraphQLResolveInfo):
    resolver = info.parent_type.fields[info.field_name].resolve
    if (
        resolver is None
        or is_default_resolver(resolver)
        or is_introspection_field(info)
    ):
        return False
    return True


def is_introspection_field(info: GraphQLResolveInfo):
    path = info.path
    while path:
        if isinstance(path.key, str) and path.key.startswith("__"):
            return True
        path = path.prev
    return False