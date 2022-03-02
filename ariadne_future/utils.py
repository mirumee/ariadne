from typing import Any, Callable, Dict, Mapping, Optional

from graphql import (
    DefinitionNode,
    GraphQLFieldResolver,
    GraphQLResolveInfo,
    ListTypeNode,
    NonNullTypeNode,
    TypeNode,
    parse,
)

from .types import FieldsDict


def parse_definition(type_name: str, schema: Any) -> DefinitionNode:
    if not isinstance(schema, str):
        raise TypeError(
            f"{type_name} class was defined with __schema__ of invalid type: "
            f"{type(schema).__name__}"
        )

    definitions = parse(schema).definitions

    if len(definitions) > 1:
        definitions_types = [type(definition).__name__ for definition in definitions]
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing more "
            f"than one GraphQL definition (found: {', '.join(definitions_types)})"
        )

    return definitions[0]


def unwrap_type_node(field_type: TypeNode):
    if isinstance(field_type, (NonNullTypeNode, ListTypeNode)):
        return unwrap_type_node(field_type.type)
    return field_type


class ResolversMixin:
    """Adds aliases and resolvers logic to GraphQL type"""

    __aliases__: Optional[Dict[str, str]] = None

    graphql_name: str
    graphql_fields: FieldsDict

    resolvers: Dict[str, GraphQLFieldResolver]

    @classmethod
    def __validate_aliases__(cls):
        if not cls.__aliases__:
            return

        invalid_aliases = set(cls.__aliases__) - set(cls.graphql_fields)
        if invalid_aliases:
            raise ValueError(
                f"{cls.__name__} class was defined with aliases for fields not in "
                f"GraphQL type: {', '.join(invalid_aliases)}"
            )

    @classmethod
    def __get_resolvers__(cls):
        aliases = cls.__aliases__ or {}
        defined_resolvers = cls.__get_defined_resolvers__()

        used_resolvers = []
        resolvers = {}

        for field_name in cls.graphql_fields:
            if aliases and field_name in aliases:
                resolver_name = aliases[field_name]
                if resolver_name in defined_resolvers:
                    used_resolvers.append(resolver_name)
                    resolvers[field_name] = defined_resolvers[resolver_name]
                else:
                    resolvers[field_name] = create_alias_resolver(resolver_name)

            elif field_name in defined_resolvers:
                used_resolvers.append(field_name)
                resolvers[field_name] = defined_resolvers[field_name]

        unused_resolvers = [
            f"resolve_{field_name}"
            for field_name in set(defined_resolvers) - set(used_resolvers)
        ]
        if unused_resolvers:
            raise ValueError(
                f"{cls.__name__} class was defined with resolvers for fields not in "
                f"GraphQL type: {', '.join(unused_resolvers)}"
            )

        return resolvers

    @classmethod
    def __get_defined_resolvers__(cls) -> Dict[str, Callable]:
        resolvers = {}
        for name in dir(cls):
            if not name.startswith("resolve_"):
                continue

            value = getattr(cls, name)
            if callable(value):
                resolvers[name[8:]] = value

        return resolvers


def create_alias_resolver(field_name: str):
    def default_aliased_field_resolver(
        source: Any, info: GraphQLResolveInfo, **args: Any
    ) -> Any:
        value = (
            source.get(field_name)
            if isinstance(source, Mapping)
            else getattr(source, field_name, None)
        )

        if callable(value):
            return value(info, **args)
        return value

    return default_aliased_field_resolver
