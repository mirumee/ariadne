from typing import Type, cast

from graphql import (
    DefinitionNode,
    DirectiveDefinitionNode,
)

from ariadne import SchemaDirectiveVisitor

from .base_type import BaseType
from .utils import parse_definition


class DirectiveTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if kwargs.pop("__abstract__", False):
            return super().__new__(cls, name, bases, kwargs)

        schema = kwargs.get("__schema__")

        graphql_def = assert_schema_defines_valid_directive(
            name, parse_definition(name, schema)
        )

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        if not kwargs.get("__visitor__"):
            raise ValueError(f"{name} class was defined without __visitor__ attribute")

        return super().__new__(cls, name, bases, kwargs)


def assert_schema_defines_valid_directive(
    type_name: str, type_def: DefinitionNode
) -> DirectiveDefinitionNode:
    if not isinstance(type_def, DirectiveDefinitionNode):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing invalid "
            f"GraphQL type definition for '{type(type_def).__name__}' "
            "(expected 'directive')"
        )

    return cast(DirectiveDefinitionNode, type_def)


class DirectiveType(BaseType, metaclass=DirectiveTypeMeta):
    __abstract__ = True
    __visitor__: Type[SchemaDirectiveVisitor]

    @staticmethod
    def __bind_to_schema__(*_):
        pass  # Binding directive to schema is noop
