from typing import Dict, Iterable, Optional, Union, cast

from graphql import (
    DefinitionNode,
    InputObjectTypeDefinitionNode,
    InputObjectTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import get_dependencies_from_input_type
from .object_type import assert_requirements_are_met
from .types import InputFieldsDict, RequirementsDict
from .utils import parse_definition

InputNodeType = Union[InputObjectTypeDefinitionNode, InputObjectTypeExtensionNode]


class InputTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        base_type = super().__new__(cls, name, bases, kwargs)
        if kwargs.pop("__abstract__", False):
            return base_type

        schema = kwargs.setdefault("__schema__", getattr(base_type, "__schema__", None))

        graphql_def = assert_schema_defines_valid_input(
            name, parse_definition(name, schema)
        )
        graphql_fields = extract_input_fields(name, graphql_def)

        args = kwargs.setdefault("__args__", getattr(base_type, "__args__", None))
        if args:
            assert_args_match_fields(name, args, graphql_fields)

        requirements_list = kwargs.setdefault(
            "__requires__", getattr(base_type, "__requires__", [])
        )
        requirements: RequirementsDict = {
            req.graphql_name: req.graphql_type for req in requirements_list
        }

        if isinstance(graphql_def, InputObjectTypeExtensionNode):
            assert_requirements_contain_extended_input(name, graphql_def, requirements)

        dependencies = get_dependencies_from_input_type(graphql_def)
        assert_requirements_are_met(name, dependencies, requirements)

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        return super().__new__(cls, name, bases, kwargs)


def assert_schema_defines_valid_input(
    type_name: str, type_def: DefinitionNode
) -> InputNodeType:
    if not isinstance(
        type_def, (InputObjectTypeDefinitionNode, InputObjectTypeExtensionNode)
    ):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing "
            f"GraphQL definition for '{type(type_def).__name__}' (expected 'type')"
        )

    return cast(InputNodeType, type_def)


def assert_args_match_fields(
    type_name: str, args: Iterable[str], fields: Iterable[str]
):
    invalid_args = set(args) - set(fields)
    if invalid_args:
        raise ValueError(
            f"{type_name} class was defined with args for fields not in "
            f"GraphQL input: {', '.join(invalid_args)}"
        )


def assert_requirements_contain_extended_input(
    type_name: str,
    type_def: InputObjectTypeExtensionNode,
    requirements: RequirementsDict,
):
    graphql_name = type_def.name.value
    if graphql_name not in requirements:
        raise ValueError(
            f"{type_name} class was defined without required GraphQL input "
            f"definition for '{graphql_name}' in __requires__"
        )

    if requirements[graphql_name] != InputObjectTypeDefinitionNode:
        raise ValueError(
            f"{type_name} requires '{graphql_name}' to be GraphQL input "
            f"but other type was provided in '__requires__'"
        )


def extract_input_fields(type_name: str, type_def: InputNodeType) -> InputFieldsDict:
    if not type_def.fields and not (
        isinstance(type_def, InputObjectTypeExtensionNode) and type_def.directives
    ):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing empty "
            f"GraphQL input definition"
        )

    return {field.name.value: field for field in type_def.fields}


class InputType(BaseType, metaclass=InputTypeMeta):
    __abstract__ = True
    __args__: Optional[Dict[str, str]]

    @classmethod
    def __bind_to_schema__(cls, schema):
        if not cls.__args__:
            return

        graphql_type = schema.type_map.get(cls.graphql_name)
        for field_name, field_target in cls.__args__.items():
            graphql_type.fields[field_name].out_name = field_target
