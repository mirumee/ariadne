from graphql import GraphQLObjectType, GraphQLScalarType, GraphQLSchema
from graphql.execution.base import ResolveInfo


def resolve_parent_field(parent, name: str, **kwargs: dict):
    if isinstance(parent, dict):
        value = parent.get(name)
    else:
        value = getattr(parent, name, None)
    if callable(value):
        return value(**kwargs)
    return value


def default_resolver(parent, info: ResolveInfo, **kwargs):
    return resolve_parent_field(parent, info.field_name, **kwargs)


def resolve_to(name: str):
    def resolver(parent, *_, **kwargs):
        return resolve_parent_field(parent, name, **kwargs)

    return resolver


def add_resolve_functions_to_schema(schema: GraphQLSchema, resolvers: dict):
    for type_name, type_object in schema.get_type_map().items():
        if isinstance(type_object, GraphQLObjectType):
            add_resolve_functions_to_object(type_name, type_object, resolvers)
        if isinstance(type_object, GraphQLScalarType):
            add_resolve_functions_to_scalar(type_name, type_object, resolvers)


def add_resolve_functions_to_object(name: str, obj: GraphQLObjectType, resolvers: dict):
    type_resolvers = resolvers.get(name, {})
    for field_name, field_object in obj.fields.items():
        field_resolver = type_resolvers.get(field_name)
        if field_resolver:
            field_object.resolver = field_resolver
        elif field_object.resolver is None:
            field_object.resolver = default_resolver


def add_resolve_functions_to_scalar(name: str, obj: GraphQLObjectType, resolvers: dict):
    scalar_resolvers = resolvers.get(name, {})

    serialize = scalar_resolvers.get("serialize", obj.serialize)
    obj.serialize = serialize

    parse_literal = scalar_resolvers.get("parse_literal", obj.parse_literal)
    obj.parse_literal = parse_literal

    parse_value = scalar_resolvers.get("parse_value", obj.parse_value)
    obj.parse_value = parse_value
