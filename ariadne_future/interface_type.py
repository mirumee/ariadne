from typing import Dict, Callable, Type, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLFieldResolver,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLTypeResolver,
    InterfaceTypeDefinitionNode,
    InterfaceTypeExtensionNode,
)

from ariadne import type_implements_interface

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_object_type
from .resolvers_mixin import ResolversMixin
from .types import FieldsDict, RequirementsDict
from .utils import parse_definition

InterfaceNodeType = Union[InterfaceTypeDefinitionNode, InterfaceTypeExtensionNode]


class InterfaceType(BaseType, ResolversMixin):
    __abstract__ = True

    graphql_name: str
    graphql_type: Union[
        Type[InterfaceTypeDefinitionNode], Type[InterfaceTypeExtensionNode]
    ]

    resolve_type: GraphQLTypeResolver
    resolvers: Dict[str, GraphQLFieldResolver]

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

        requirements = cls.__get_requirements__()
        cls.__validate_requirements_contain_extended_type__(graphql_def, requirements)

        dependencies = cls.__get_dependencies__(graphql_def)
        cls.__validate_requirements__(requirements, dependencies)

        if callable(cls.__fields_args__):
            cls.__fields_args__ = cls.__fields_args__(cls.graphql_fields, True)

        cls.__validate_fields_args__()

        if callable(cls.__aliases__):
            cls.__aliases__ = cls.__aliases__(cls.graphql_fields)

        cls.__validate_aliases__()
        cls.resolvers = cls.__get_resolvers__()

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> InterfaceNodeType:
        if not isinstance(
            type_def, (InterfaceTypeDefinitionNode, InterfaceTypeExtensionNode)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ without "
                "GraphQL interface"
            )

        return cast(InterfaceNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: InterfaceNodeType, requirements: RequirementsDict
    ):
        if not isinstance(type_def, InterfaceTypeExtensionNode):
            return

        graphql_name = type_def.name.value
        if graphql_name not in requirements:
            raise ValueError(
                f"{cls.__name__} graphql type was defined without required GraphQL "
                f"type definition for '{graphql_name}' in __requires__"
            )

        if requirements[graphql_name] != InterfaceTypeDefinitionNode:
            raise ValueError(
                f"{cls.__name__} requires '{graphql_name}' to be GraphQL interface "
                f"but other type was provided in '__requires__'"
            )

    @classmethod
    def __get_fields__(cls, type_def: InterfaceNodeType) -> FieldsDict:
        if not type_def.fields and not (
            isinstance(type_def, InterfaceTypeExtensionNode)
            and (type_def.directives or type_def.interfaces)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing empty "
                f"GraphQL interface definition"
            )

        return {field.name.value: field for field in type_def.fields}

    @classmethod
    def __get_defined_resolvers__(cls) -> Dict[str, Callable]:
        resolvers = super().__get_defined_resolvers__()
        resolvers.pop("type", None)
        return resolvers

    @classmethod
    def __get_dependencies__(cls, type_def: InterfaceNodeType) -> Dependencies:
        return get_dependencies_from_object_type(type_def)

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        graphql_type = cast(GraphQLInterfaceType, schema.type_map.get(cls.graphql_name))
        graphql_type.resolve_type = cls.resolve_type

        for type_ in schema.type_map.values():
            if not type_implements_interface(cls.graphql_name, type_):
                continue

            type_ = cast(GraphQLObjectType, type_)
            for field_name, field_resolver in cls.resolvers.items():
                if not type_.fields[field_name].resolve:
                    type_.fields[field_name].resolve = field_resolver
