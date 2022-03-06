from typing import Callable, Dict, Optional, Union

from graphql import GraphQLFieldResolver

from .types import FieldsDict
from .utils import create_alias_resolver

Aliases = Dict[str, str]
FieldsArgs = Dict[str, Dict[str, str]]


class ResolversMixin:
    """Adds aliases and resolvers logic to GraphQL type"""

    __aliases__: Optional[Union[Aliases, Callable[..., Aliases]]] = None
    __fields_args__: Optional[Union[FieldsArgs, Callable[..., FieldsArgs]]] = None

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
    def __validate_fields_args__(cls):
        if not cls.__fields_args__:
            return

        invalid_fields = set(cls.__fields_args__) - set(cls.graphql_fields)
        if invalid_fields:
            raise ValueError(
                f"{cls.__name__} class was defined with fields args mappings "
                f"for fields not in GraphQL type: {', '.join(invalid_fields)}"
            )

        for field_name, field_args in cls.__fields_args__.items():
            defined_args = [
                arg.name.value for arg in cls.graphql_fields[field_name].arguments
            ]
            invalid_args = set(field_args) - set(defined_args)
            if invalid_args:
                raise ValueError(
                    f"{cls.__name__} class was defined with args mappings not in "
                    f"not in '{field_name}' field: {', '.join(invalid_args)}"
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
