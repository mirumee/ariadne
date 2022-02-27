from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLTypeResolver,
    InterfaceTypeDefinitionNode,
    InterfaceTypeExtensionNode,
)

from ariadne.utils import type_implements_interface

from .base_type import BaseType
from .dependencies import get_dependencies_from_object_type
from .object_type import (
    assert_aliases_match_fields,
    assert_requirements_are_met,
    get_defined_resolvers,
    get_final_resolvers,
)
from .types import FieldsDict, RequirementsDict
from .utils import parse_definition

InterfaceNodeType = Union[InterfaceTypeDefinitionNode, InterfaceTypeExtensionNode]


class InterfaceTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if kwargs.pop("__abstract__", False):
            return super().__new__(cls, name, bases, kwargs)

        schema = kwargs.get("__schema__")

        graphql_def = assert_schema_defines_valid_interface(
            name, parse_definition(name, schema)
        )
        graphql_fields = extract_graphql_fields(name, graphql_def)

        requirements: RequirementsDict = {
            req.graphql_name: req.graphql_type
            for req in kwargs.setdefault("__requires__", [])
        }

        if isinstance(graphql_def, InterfaceTypeExtensionNode):
            assert_requirements_contain_extended_interface(
                name, graphql_def, requirements
            )

        dependencies = get_dependencies_from_object_type(graphql_def)
        assert_requirements_are_met(name, dependencies, requirements)

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        aliases = kwargs.setdefault("__aliases__", {})
        assert_aliases_match_fields(name, aliases, graphql_fields)

        defined_resolvers = get_defined_resolvers(kwargs)
        defined_resolvers.pop("type", None)

        kwargs["_resolvers"] = get_final_resolvers(
            name, graphql_fields, aliases, defined_resolvers
        )

        return super().__new__(cls, name, bases, kwargs)


def assert_schema_defines_valid_interface(
    type_name: str, type_def: DefinitionNode
) -> InterfaceNodeType:
    if not isinstance(
        type_def, (InterfaceTypeDefinitionNode, InterfaceTypeExtensionNode)
    ):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing "
            f"GraphQL definition for '{type(type_def).__name__}' "
            "(expected 'interface')"
        )

    return cast(InterfaceNodeType, type_def)


def assert_requirements_contain_extended_interface(
    type_name: str,
    type_def: InterfaceTypeExtensionNode,
    requirements: RequirementsDict,
):
    graphql_name = type_def.name.value
    if graphql_name not in requirements:
        raise ValueError(
            f"{type_name} class was defined without required GraphQL interface "
            f"definition for '{graphql_name}' in __requires__"
        )

    if requirements[graphql_name] != InterfaceTypeDefinitionNode:
        raise ValueError(
            f"{type_name} requires '{graphql_name}' to be GraphQL interface "
            f"but other type was provided in '__requires__'"
        )


def extract_graphql_fields(type_name: str, type_def: InterfaceNodeType) -> FieldsDict:
    if not type_def.fields and not (
        isinstance(type_def, InterfaceTypeExtensionNode)
        and (type_def.directives or type_def.interfaces)
    ):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing empty "
            f"GraphQL interface definition"
        )

    return {field.name.value: field for field in type_def.fields}


class InterfaceType(BaseType, metaclass=InterfaceTypeMeta):
    __abstract__ = True
    __schema__: str
    __requires__: List[Type[BaseType]]
    __aliases__: Optional[Dict[str, str]]

    graphql_name: str
    graphql_type: InterfaceNodeType
    resolve_type: Optional[GraphQLTypeResolver] = None

    _resolvers: Dict[str, Callable[..., Any]]

    @classmethod
    def __bind_to_schema__(cls, schema):
        if cls.resolve_type:
            graphql_type = schema.type_map.get(cls.graphql_name)
            graphql_type.resolve_type = cls.resolve_type

        for graphql_type in schema.type_map.values():
            if not type_implements_interface(cls.graphql_name, graphql_type):
                continue

            for field_name, field_resolver in cls._resolvers.items():
                if not graphql_type.fields[field_name].resolve:
                    graphql_type.fields[field_name].resolve = field_resolver
