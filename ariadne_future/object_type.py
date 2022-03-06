from typing import Dict, Type, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLFieldResolver,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_object_type
from .resolvers_mixin import ResolversMixin
from .types import FieldsDict, RequirementsDict
from .utils import parse_definition

ObjectNodeType = Union[ObjectTypeDefinitionNode, ObjectTypeExtensionNode]


class ObjectType(BaseType, ResolversMixin):
    __abstract__ = True

    graphql_name: str
    graphql_type: Union[Type[ObjectTypeDefinitionNode], Type[ObjectTypeExtensionNode]]

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
    def __validate_schema__(cls, type_def: DefinitionNode) -> ObjectNodeType:
        if not isinstance(
            type_def, (ObjectTypeDefinitionNode, ObjectTypeExtensionNode)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ without GraphQL type"
            )

        if type_def.name.value == "Subscription":
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing "
                f"GraphQL definition for 'type Subscription' which is only supported "
                "by subsclassess of 'SubscriptionType'"
            )

        return cast(ObjectNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: ObjectNodeType, requirements: RequirementsDict
    ):
        if not isinstance(type_def, ObjectTypeExtensionNode):
            return

        graphql_name = type_def.name.value
        if graphql_name not in requirements:
            raise ValueError(
                f"{cls.__name__} graphql type was defined without required GraphQL "
                f"type definition for '{graphql_name}' in __requires__"
            )

        if requirements[graphql_name] != ObjectTypeDefinitionNode:
            raise ValueError(
                f"{cls.__name__} requires '{graphql_name}' to be GraphQL type "
                f"but other type was provided in '__requires__'"
            )

    @classmethod
    def __get_fields__(cls, type_def: ObjectNodeType) -> FieldsDict:
        if not type_def.fields and not (
            isinstance(type_def, ObjectTypeExtensionNode)
            and (type_def.directives or type_def.interfaces)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing "
                f"empty GraphQL type definition"
            )

        return {field.name.value: field for field in type_def.fields}

    @classmethod
    def __get_dependencies__(cls, type_def: ObjectNodeType) -> Dependencies:
        return get_dependencies_from_object_type(type_def)

    @classmethod
    def __bind_to_schema__(cls, schema):
        graphql_type = schema.type_map.get(cls.graphql_name)

        for field_name, field_resolver in cls.resolvers.items():
            graphql_type.fields[field_name].resolve = field_resolver
