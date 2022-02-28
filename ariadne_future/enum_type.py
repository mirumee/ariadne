from enum import Enum
from typing import Iterable, List, Optional, Type, Union, cast

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

ScalarNodeType = Union[EnumTypeDefinitionNode, EnumTypeExtensionNode]


class EnumTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if kwargs.pop("__abstract__", False):
            return super().__new__(cls, name, bases, kwargs)

        schema = kwargs.get("__schema__")

        graphql_def = assert_schema_defines_valid_enum(
            name, parse_definition(name, schema)
        )

        if isinstance(graphql_def, EnumTypeExtensionNode):
            requirements: RequirementsDict = {
                req.graphql_name: req.graphql_type
                for req in kwargs.setdefault("__requires__", [])
            }
            assert_requirements_contain_extended_enum(name, graphql_def, requirements)

        values = extract_graphql_values(name, graphql_def)
        enum = kwargs.setdefault("__enum__", None)
        if enum:
            assert_enum_members_match_values(name, enum, values)

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        return super().__new__(cls, name, bases, kwargs)


def assert_schema_defines_valid_enum(
    type_name: str, type_def: DefinitionNode
) -> ScalarNodeType:
    if not isinstance(type_def, (EnumTypeDefinitionNode, EnumTypeExtensionNode)):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing invalid "
            f"GraphQL type definition for '{type(type_def).__name__}' (expected 'enum')"
        )

    return cast(ScalarNodeType, type_def)


def assert_requirements_contain_extended_enum(
    type_name: str,
    type_def: EnumTypeExtensionNode,
    requirements: RequirementsDict,
):
    graphql_name = type_def.name.value
    if graphql_name not in requirements:
        raise ValueError(
            f"{type_name} graphql type was defined without required GraphQL enum "
            f"definition for '{graphql_name}' in __requires__"
        )

    if requirements[graphql_name] != EnumTypeDefinitionNode:
        raise ValueError(
            f"{type_name} requires '{graphql_name}' to be GraphQL enum "
            f"but other type was provided in '__requires__'"
        )


def extract_graphql_values(type_name: str, type_def: ScalarNodeType) -> List[str]:
    if not type_def.values and not (
        isinstance(type_def, EnumTypeExtensionNode) and type_def.directives
    ):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing empty "
            f"GraphQL enum definition"
        )

    return [value.name.value for value in type_def.values]


def assert_enum_members_match_values(
    type_name: str, enum: Union[Type[Enum], dict], values: Iterable[str]
):
    if isinstance(enum, dict):
        enum_keys = set(enum.keys())
    else:
        enum_keys = set(enum.__members__.keys())

    missing_keys = set(values) - enum_keys
    if missing_keys:
        raise ValueError(
            f"{type_name} class was defined with __enum__ missing following "
            f"items required by GraphQL definition: {', '.join(missing_keys)}"
        )

    extra_keys = enum_keys - set(values)
    if extra_keys:
        raise ValueError(
            f"{type_name} class was defined with __enum__ containing extra "
            f"items missing in GraphQL definition: {', '.join(extra_keys)}"
        )


class EnumType(BaseType, metaclass=EnumTypeMeta):
    __abstract__ = True
    __enum__: Optional[Union[Type[Enum], dict]]

    graphql_type: ScalarNodeType

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
