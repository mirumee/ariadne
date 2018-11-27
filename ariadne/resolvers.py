from graphql.type import GraphQLResolveInfo

from .utils import convert_graphql_name_to_python_name


class Resolvers:
    def __init__(self, type_name):
        self.type_name = type_name
        self.resolvers = {}

    def register(self, field_name):
        def register_as_resolver(f):
            self.resolvers[field_name] = f
            return f

        return register_as_resolver

    def alias(self, field_name, attr_name):
        self.resolvers[field_name] = resolve_to(attr_name)

    def get(self, type_name, default=None):
        if type_name == self.type_name:
            return ResolversFactory(self.resolvers)
        return default


class ResolversFactory:
    def __init__(self, resolvers):
        self.resolvers = resolvers

    def get(self, field_name):
        if field_name in self.resolvers:
            return self.resolvers[field_name]

        python_name = convert_graphql_name_to_python_name(field_name)
        return resolve_to(python_name)


def resolve_parent_field(parent, name: str, **kwargs: dict):
    if isinstance(parent, dict):
        value = parent.get(name)
    else:
        value = getattr(parent, name, None)
    if callable(value):
        return value(**kwargs)
    return value


def default_resolver(parent, info: GraphQLResolveInfo, **kwargs):
    return resolve_parent_field(parent, info.field_name, **kwargs)


def resolve_to(name: str):
    def resolver(parent, *_, **kwargs):
        return resolve_parent_field(parent, name, **kwargs)
    return resolver
