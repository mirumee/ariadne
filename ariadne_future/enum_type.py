from enum import Enum
from typing import List, Optional, Type, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLSchema,
    EnumTypeDefinitionNode,
    EnumTypeExtensionNode,
)

import ariadne

from .base_type import BaseType
from .types import RequirementsDict
from .utils import parse_definition

EnumNodeType = Union[EnumTypeDefinitionNode, EnumTypeExtensionNode]


class EnumType(BaseType):
    __abstract__ = True
    __enum__: Optional[Union[Type[Enum], dict]] = None

    graphql_type: Union[Type[EnumTypeDefinitionNode], Type[EnumTypeExtensionNode]]

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

        values = cls.__get_values__(graphql_def)
        cls.__validate_values__(values)

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> EnumNodeType:
        if not isinstance(type_def, (EnumTypeDefinitionNode, EnumTypeExtensionNode)):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ without GraphQL enum"
            )

        return cast(EnumNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: EnumNodeType, requirements: RequirementsDict
    ):
        if not isinstance(type_def, EnumTypeExtensionNode):
            return

        graphql_name = type_def.name.value
        if graphql_name not in requirements:
            raise ValueError(
                f"{cls.__name__} graphql type was defined without required GraphQL "
                f"type definition for '{graphql_name}' in __requires__"
            )

        if requirements[graphql_name] != EnumTypeDefinitionNode:
            raise ValueError(
                f"{cls.__name__} requires '{graphql_name}' to be GraphQL enum "
                f"but other type was provided in '__requires__'"
            )

    @classmethod
    def __get_values__(cls, type_def: EnumNodeType) -> List[str]:
        if not type_def.values and not (
            isinstance(type_def, EnumTypeExtensionNode) and type_def.directives
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing "
                f"empty, GraphQL enum definition"
            )

        return [value.name.value for value in type_def.values]

    @classmethod
    def __validate_values__(cls, values: List[str]):
        if not cls.__enum__:
            return

        if isinstance(cls.__enum__, dict):
            enum_keys = set(cls.__enum__.keys())
        else:
            enum_keys = set(cls.__enum__.__members__.keys())

        missing_keys = set(values) - enum_keys
        if missing_keys:
            raise ValueError(
                f"{cls.__name__} class was defined with __enum__ missing following "
                f"items required by GraphQL definition: {', '.join(missing_keys)}"
            )

        extra_keys = enum_keys - set(values)
        if extra_keys:
            raise ValueError(
                f"{cls.__name__} class was defined with __enum__ containing extra "
                f"items missing in GraphQL definition: {', '.join(extra_keys)}"
            )

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        if cls.__enum__:
            bindable = ariadne.EnumType(cls.graphql_name, cls.__enum__)
            bindable.bind_to_schema(schema)

    @classmethod
    def __bind_to_default_values__(cls, schema: GraphQLSchema):
        if cls.__enum__:
            bindable = ariadne.EnumType(cls.graphql_name, cls.__enum__)
            bindable.bind_to_default_values(schema)
