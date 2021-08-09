from graphql import GraphQLResolveInfo, ResponsePath

from ...resolvers import is_default_resolver


def format_path(path: ResponsePath):
    elements = []
    while path:
        elements.append(path.key)
        path = path.prev
    return elements[::-1]


def should_trace(info: GraphQLResolveInfo, trace_default_resolver: bool = False):
    if info.field_name not in info.parent_type.fields:
        return False

    resolver = info.parent_type.fields[info.field_name].resolve
    if trace_default_resolver:
        default_resolver_bool = False
    else:
        default_resolver_bool = is_default_resolver(resolver)
    return not (default_resolver_bool or is_introspection_field(info))


def is_introspection_field(info: GraphQLResolveInfo):
    path = info.path
    while path:
        if isinstance(path.key, str) and is_introspection_key(path.key):
            return True
        path = path.prev
    return False


def is_introspection_key(key: str):
    return key.lower() in [
        "__schema",
        "__directive",
        "__directivelocation",
        "__type",
        "__field",
        "__inputvalue",
        "__enumvalue",
        "__typekind",
    ]  # from graphql.type.introspection.introspection_types
