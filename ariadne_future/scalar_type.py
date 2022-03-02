from typing import Optional, Type, Union, cast

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


class ScalarType(BaseType):
    __abstract__ = True

    graphql_type: Union[Type[ScalarTypeDefinitionNode], Type[ScalarTypeExtensionNode]]

    serialize: Optional[GraphQLScalarSerializer] = None
    parse_value: Optional[GraphQLScalarValueParser] = None
    parse_literal: Optional[GraphQLScalarLiteralParser] = None

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

        requirements = cls.__get_requirements__()
        cls.__validate_requirements_contain_extended_type__(graphql_def, requirements)

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> ScalarNodeType:
        if not isinstance(
            type_def, (ScalarTypeDefinitionNode, ScalarTypeExtensionNode)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ "
                "without GraphQL scalar"
            )

        return cast(ScalarNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: ScalarNodeType, requirements: RequirementsDict
    ):
        if not isinstance(type_def, ScalarTypeExtensionNode):
            return

        graphql_name = type_def.name.value
        if graphql_name not in requirements:
            raise ValueError(
                f"{cls.__name__} graphql type was defined without required GraphQL "
                f"scalar, definition for '{graphql_name}' in __requires__"
            )

        if requirements[graphql_name] != ScalarTypeDefinitionNode:
            raise ValueError(
                f"{cls.__name__} requires '{graphql_name}' to be GraphQL scalar "
                f"but other type was provided in '__requires__'"
            )

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
