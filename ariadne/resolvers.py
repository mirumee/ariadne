from collections.abc import Mapping
from typing import Any, Optional

from graphql import default_field_resolver
from graphql.type import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLSchema,
)

from .types import Resolver, SchemaBindable
from .utils import convert_camel_case_to_snake


class FallbackResolversSetter(SchemaBindable):
    """Bindable that recursively scans GraphQL schema for fields and explicitly
    sets their resolver to `graphql.default_field_resolver` package if
    they don't have any resolver set yet.

    > **Deprecated:** This class doesn't provide any utility for developers and
    only serves as a base for `SnakeCaseFallbackResolversSetter` which is being
    replaced by what we believe to be a better solution.
    >
    > Because of this we are deprecating this utility. It will be removed in future
    Ariadne release.
    """

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Scans GraphQL schema for types with fields that don't have set resolver."""
        for type_object in schema.type_map.values():
            if isinstance(type_object, GraphQLObjectType):
                self.add_resolvers_to_object_fields(type_object)

    def add_resolvers_to_object_fields(self, type_object: GraphQLObjectType) -> None:
        """Sets explicit default resolver on a fields of an object that don't have any."""  # noqa: E501
        for field_name, field_object in type_object.fields.items():
            self.add_resolver_to_field(field_name, field_object)

    def add_resolver_to_field(self, _: str, field_object: GraphQLField) -> None:
        """Sets `default_field_resolver` as a resolver on a field that doesn't have any."""  # noqa: E501
        if field_object.resolve is None:
            field_object.resolve = default_field_resolver


class SnakeCaseFallbackResolversSetter(FallbackResolversSetter):
    """Subclass of `FallbackResolversSetter` that uses case-converting resolver
    instead of `default_field_resolver`.

    > **Deprecated:** Use `convert_names_case` from `make_executable_schema`
    instead.
    """

    def add_resolver_to_field(
        self, field_name: str, field_object: GraphQLField
    ) -> None:
        """Sets case converting resolver on a field that doesn't have any."""
        if field_object.resolve is None:
            field_name = convert_camel_case_to_snake(field_name)
            field_object.resolve = resolve_to(field_name)


"""
Bindable instance of `FallbackResolversSetter`.

> **Deprecated:** This utility will be removed in future Ariadne release.
> 
> See `FallbackResolversSetter` for details.
"""
fallback_resolvers = FallbackResolversSetter()

"""
Bindable instance of `SnakeCaseFallbackResolversSetter`.

> **Deprecated:** Use `convert_names_case` from `make_executable_schema` 
instead.
"""
snake_case_fallback_resolvers = SnakeCaseFallbackResolversSetter()


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


def is_default_resolver(resolver: Optional[Resolver]) -> bool:
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
