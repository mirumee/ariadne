from typing import Type, cast

from graphql import (
    DefinitionNode,
    DirectiveDefinitionNode,
)

from ariadne import SchemaDirectiveVisitor

from .base_type import BaseType
from .utils import parse_definition


class DirectiveType(BaseType):
    __abstract__ = True
    __visitor__: Type[SchemaDirectiveVisitor]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.__dict__.get("__abstract__"):
            return

        cls.__abstract__ = False

        graphql_def = cls.__validate_schema__(
            parse_definition(cls.__name__, cls.__schema__)
        )

        cls.graphql_name = graphql_def.name.value
        cls.graphql_type = type(graphql_def)

        cls.__validate_visitor__()

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> DirectiveDefinitionNode:
        if not isinstance(type_def, DirectiveDefinitionNode):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ "
                "without GraphQL directive"
            )

        return cast(DirectiveDefinitionNode, type_def)

    @classmethod
    def __validate_visitor__(cls):
        if not getattr(cls, "__visitor__", None):
            raise AttributeError(
                f"{cls.__name__} class was defined without __visitor__ attribute"
            )

    @staticmethod
    def __bind_to_schema__(*_):
        pass  # Binding directive to schema is noop
