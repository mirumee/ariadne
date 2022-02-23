from typing import Optional, cast

from graphql import (
    DefinitionNode,
    GraphQLScalarSerializer,
    GraphQLScalarType,
    GraphQLScalarLiteralParser,
    GraphQLScalarValueParser,
    GraphQLSchema,
    ScalarTypeDefinitionNode,
)

from .base_type import BaseType
from .utils import parse_definition


class ScalarMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if kwargs.pop("__abstract__", False):
            return super().__new__(cls, name, bases, kwargs)

        schema = kwargs.get("__schema__")

        graphql_def = assert_valid_scalar_schema(name, parse_definition(name, schema))

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        return super().__new__(cls, name, bases, kwargs)


def assert_valid_scalar_schema(
    type_name: str, type_def: DefinitionNode
) -> ScalarTypeDefinitionNode:
    if not isinstance(type_def, ScalarTypeDefinitionNode):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing invalid "
            f"GraphQL type definition: {type(type_def).__name__} (expected scalar)"
        )

    return cast(ScalarTypeDefinitionNode, type_def)


class Scalar(BaseType, metaclass=ScalarMeta):
    __abstract__ = True

    serialize: Optional[GraphQLScalarSerializer] = None
    parse_value: Optional[GraphQLScalarValueParser] = None
    parse_literal: Optional[GraphQLScalarLiteralParser] = None

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        graphql_type = cast(GraphQLScalarType, schema.type_map.get(cls.graphql_name))

        # See mypy bug https://github.com/python/mypy/issues/2427
        if cls.serialize:
            graphql_type.serialize = cls.serialize  # type: ignore
        if cls.parse_value:
            graphql_type.parse_value = cls.parse_value  # type: ignore
        if cls.parse_literal:
            graphql_type.parse_literal = cls.parse_literal  # type: ignore
