from typing import Callable, Dict, Optional, Union, cast

from graphql import (
    DefinitionNode,
    InputObjectTypeDefinitionNode,
    InputObjectTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_input_type
from .types import InputFieldsDict, RequirementsDict
from .utils import parse_definition

Args = Dict[str, str]
InputNodeType = Union[InputObjectTypeDefinitionNode, InputObjectTypeExtensionNode]


class InputType(BaseType):
    __abstract__ = True
    __args__: Optional[Union[Args, Callable[..., Args]]] = None

    graphql_fields: InputFieldsDict

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
        cls.graphql_fields = cls.__get_fields__(graphql_def)

        if callable(cls.__args__):
            # pylint: disable=not-callable
            cls.__args__ = cls.__args__(cls.graphql_fields)

        cls.__validate_args__()

        requirements = cls.__get_requirements__()
        cls.__validate_requirements_contain_extended_type__(graphql_def, requirements)

        dependencies = cls.__get_dependencies__(graphql_def)
        cls.__validate_requirements__(requirements, dependencies)

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> InputNodeType:
        if not isinstance(
            type_def, (InputObjectTypeDefinitionNode, InputObjectTypeExtensionNode)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ without GraphQL input"
            )

        return cast(InputNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: InputNodeType, requirements: RequirementsDict
    ):
        if not isinstance(type_def, InputObjectTypeExtensionNode):
            return

        graphql_name = type_def.name.value
        if graphql_name not in requirements:
            raise ValueError(
                f"{cls.__name__} graphql type was defined without required GraphQL "
                f"type definition for '{graphql_name}' in __requires__"
            )

        if requirements[graphql_name] != InputObjectTypeDefinitionNode:
            raise ValueError(
                f"{cls.__name__} requires '{graphql_name}' to be GraphQL input "
                f"but other type was provided in '__requires__'"
            )

    @classmethod
    def __get_fields__(cls, type_def: InputNodeType) -> InputFieldsDict:
        if not type_def.fields and not (
            isinstance(type_def, InputObjectTypeExtensionNode) and type_def.directives
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing empty "
                f"GraphQL input definition"
            )

        return {field.name.value: field for field in type_def.fields}

    @classmethod
    def __validate_args__(cls):
        if not cls.__args__:
            return

        invalid_args = set(cls.__args__) - set(cls.graphql_fields)
        if invalid_args:
            raise ValueError(
                f"{cls.__name__} class was defined with args for fields not in "
                f"GraphQL input: {', '.join(invalid_args)}"
            )

    @classmethod
    def __get_dependencies__(cls, type_def: InputNodeType) -> Dependencies:
        return get_dependencies_from_input_type(type_def)

    @classmethod
    def __bind_to_schema__(cls, schema):
        if not cls.__args__:
            return

        graphql_type = schema.type_map.get(cls.graphql_name)
        for field_name, field_target in cls.__args__.items():
            graphql_type.fields[field_name].out_name = field_target
