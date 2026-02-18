from collections.abc import Mapping
from typing import Any

from graphql import default_field_resolver
from graphql.type import (
    GraphQLResolveInfo,
)

from .types import Resolver


def resolve_parent_field(parent: Any, field_name: str) -> Any:
    value = parent
    for name in field_name.split("."):
        if isinstance(value, Mapping):
            value = value.get(name)
        else:
            value = getattr(value, name, None)

        if value is None:
            break
    return value


def resolve_to(attr_name: str) -> Resolver:
    """Create a resolver that resolves to given attribute or dict key.

    Returns a resolver function that can be used as resolver.

    Usually not used directly  but through higher level features like aliases
    or schema names conversion.

    # Required arguments

    `attr_name`: a `str` with name of attribute or `dict` key to return from
    resolved object.
    """

    def resolver(parent: Any, info: GraphQLResolveInfo, **kwargs) -> Any:
        value = resolve_parent_field(parent, attr_name)
        if callable(value):
            return value(info, **kwargs)
        return value

    resolver._ariadne_alias_resolver = True  # type: ignore
    return resolver


def is_default_resolver(resolver: Resolver | None) -> bool:
    """Test if resolver function is default resolver implemented by
    `graphql-core` or Ariadne.

    Returns `True` if resolver function is `None`, `graphql.default_field_resolver`
    or was created by Ariadne's `resolve_to` utility. Returns `False` otherwise.

    `True` is returned for `None` because query executor defaults to the
    `graphql.default_field_resolver` is there's no resolver function set on a
    field.

    # Required arguments

    `resolver`: a function `None` to test or `None`.
    """
    if not resolver or resolver == default_field_resolver:
        return True
    return hasattr(resolver, "_ariadne_alias_resolver")
