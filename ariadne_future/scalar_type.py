from typing import Optional, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLScalarSerializer,
    GraphQLScalarType,
    GraphQLScalarLiteralParser,
    GraphQLScalarValueParser,
    GraphQLSchema,
    ScalarTypeDefinitionNode,
    ScalarTypeExtensionNode,
)

from .base_type import BaseType
from .types import RequirementsDict
from .utils import parse_definition

ScalarNodeType = Union[ScalarTypeDefinitionNode, ScalarTypeExtensionNode]


class ScalarTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if kwargs.pop("__abstract__", False):
            return super().__new__(cls, name, bases, kwargs)

        schema = kwargs.get("__schema__")

        graphql_def = assert_schema_defines_valid_scalar(
            name, parse_definition(name, schema)
        )

        if isinstance(graphql_def, ScalarTypeExtensionNode):
            requirements: RequirementsDict = {
                req.graphql_name: req.graphql_type
                for req in kwargs.setdefault("__requires__", [])
            }
            assert_requirements_contain_extended_type(name, graphql_def, requirements)

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        return super().__new__(cls, name, bases, kwargs)


def assert_schema_defines_valid_scalar(
    type_name: str, type_def: DefinitionNode
) -> ScalarNodeType:
    if not isinstance(type_def, (ScalarTypeDefinitionNode, ScalarTypeExtensionNode)):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing invalid "
            f"GraphQL type definition for '{type(type_def).__name__}' (expected 'scalar')"
        )

    return cast(ScalarNodeType, type_def)


def assert_requirements_contain_extended_type(
    type_name: str,
    type_def: ScalarTypeExtensionNode,
    requirements: RequirementsDict,
):
    graphql_name = type_def.name.value
    if graphql_name not in requirements:
        raise ValueError(
            f"{type_name} graphql type was defined without required GraphQL scalar "
            f"definition for '{graphql_name}' in __requires__"
        )

    if requirements[graphql_name] != ScalarTypeDefinitionNode:
        raise ValueError(
            f"{type_name} requires '{graphql_name}' to be GraphQL scalar "
            f"but other type was provided in '__requires__'"
        )


class ScalarType(BaseType, metaclass=ScalarTypeMeta):
    __abstract__ = True

    graphql_type: ScalarNodeType

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
