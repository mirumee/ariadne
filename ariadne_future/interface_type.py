from typing import Callable, Dict, Type, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLTypeResolver,
    InterfaceTypeDefinitionNode,
    InterfaceTypeExtensionNode,
)

from ariadne import type_implements_interface

from .object_type import ObjectType
from .types import FieldsDict, RequirementsDict

InterfaceNodeType = Union[InterfaceTypeDefinitionNode, InterfaceTypeExtensionNode]


class InterfaceType(ObjectType):
    __abstract__ = True

    graphql_type: Union[
        Type[InterfaceTypeDefinitionNode], Type[InterfaceTypeExtensionNode]
    ]

    resolve_type: GraphQLTypeResolver

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
