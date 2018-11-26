from graphql import GraphQLObjectType, GraphQLScalarType, GraphQLSchema
from graphql.type import GraphQLResolveInfo


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

        python_name = ""
        for i, c in enumerate(field_name.lower()):
            if c != field_name[i]:
                python_name += "_"
            python_name += c
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


def add_resolve_functions_to_schema(schema: GraphQLSchema, resolvers: dict):
    for type_name, type_object in schema.type_map.items():
        if isinstance(type_object, GraphQLObjectType):
            add_resolve_functions_to_object(type_name, type_object, resolvers)
        if isinstance(type_object, GraphQLScalarType):
            add_resolve_functions_to_scalar(type_name, type_object, resolvers)


def add_resolve_functions_to_object(name: str, obj: GraphQLObjectType, resolvers: dict):
    type_resolvers = resolvers.get(name, {})
    for field_name, field_object in obj.fields.items():
        field_resolver = type_resolvers.get(field_name)
        if field_resolver:
            field_object.resolve = field_resolver
        elif field_object.resolve is None:
            field_object.resolve = default_resolver


def add_resolve_functions_to_scalar(name: str, obj: GraphQLObjectType, resolvers: dict):
    scalar_resolvers = resolvers.get(name, {})

    serialize = scalar_resolvers.get("serialize", obj.serialize)
    obj.serialize = serialize

    parse_literal = scalar_resolvers.get("parse_literal", obj.parse_literal)
    obj.parse_literal = parse_literal

    parse_value = scalar_resolvers.get("parse_value", obj.parse_value)
    obj.parse_value = parse_value
