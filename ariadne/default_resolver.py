from graphql.execution.base import ResolveInfo


def default_resolver(context, info: ResolveInfo):
    if isinstance(context, dict):
        return context.get(info.field_name)
    return getattr(context, info.field_name, None)
