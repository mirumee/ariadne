from graphql.type import GraphQLResolveInfo


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


class ResolverMap:
    def __init__(self, name: str):
        self.name = name
        self._resolvers = {}

    def field(self, name: str):
        def register_resolver(f):
            self._resolvers[name] = f
            return f

        return register_resolver

    def alias(self, name: str, to: str):
        self._resolvers[name] = resolve_to(to)

    def bind_to_schema(self, schema):
        graphql_type = schema.type_map.get(self.name)
        if not graphql_type:
            raise ValueError("Type %s is not defined in schema" % self.name)

        for field, resolver in self._resolvers.items():
            if field not in graphql_type.fields:
                raise ValueError(
                    "Field %s is not defined on type %s" % (field, self.name)
                )

            graphql_type.fields[field].resolve = resolver
