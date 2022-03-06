from typing import Dict, Optional, Type, Union, cast

from graphql import (
    DefinitionNode,
    FieldDefinitionNode,
    GraphQLFieldResolver,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_object_type
from .types import RequirementsDict
from .utils import parse_definition

ObjectNodeType = Union[ObjectTypeDefinitionNode, ObjectTypeExtensionNode]


class MutationType(BaseType):
    __abstract__ = True
    __args__: Optional[Dict[str, str]] = None

    graphql_name = "Mutation"
    graphql_type: Union[Type[ObjectTypeDefinitionNode], Type[ObjectTypeExtensionNode]]

    mutation_name: str
    resolve_mutation: GraphQLFieldResolver

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

        field = cls.__get_field__(graphql_def)
        cls.mutation_name = field.name.value

        requirements = cls.__get_requirements__()
        cls.__validate_requirements_contain_extended_type__(graphql_def, requirements)

        dependencies = cls.__get_dependencies__(graphql_def)
        cls.__validate_requirements__(requirements, dependencies)

        cls.__validate_args__(field)
        cls.__validate_resolve_mutation__()

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> ObjectNodeType:
        if not isinstance(
            type_def, (ObjectTypeDefinitionNode, ObjectTypeExtensionNode)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ without GraphQL type"
            )

        if type_def.name.value != "Mutation":
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing "
                f"GraphQL definition for 'type {type_def.name.value}' while "
                "'type Mutation' was expected"
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
    def __get_field__(cls, type_def: ObjectNodeType) -> FieldDefinitionNode:
        if not type_def.fields:
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing "
                f"empty GraphQL type definition"
            )

        if len(type_def.fields) != 1:
            raise ValueError(
                f"{cls.__name__} class subclasses 'MutationType' class which "
                "requires __schema__ to define exactly one field"
            )

        return type_def.fields[0]

    @classmethod
    def __get_dependencies__(cls, type_def: ObjectNodeType) -> Dependencies:
        return get_dependencies_from_object_type(type_def)

    @classmethod
    def __validate_args__(cls, field: FieldDefinitionNode):
        if not cls.__args__:
            return

        field_args = [arg.name.value for arg in field.arguments]
        invalid_args = set(cls.__args__) - set(field_args)
        if invalid_args:
            raise ValueError(
                f"{cls.__name__} class was defined with args not on "
                f"'{field.name.value}' GraphQL field: {', '.join(invalid_args)}"
            )

    @classmethod
    def __validate_resolve_mutation__(cls):
        resolver = getattr(cls, "resolve_mutation", None)
        if not resolver:
            raise AttributeError(
                f"{cls.__name__} class was defined without required "
                "'resolve_mutation' attribute"
            )

        if not callable(resolver):
            raise TypeError(
                f"{cls.__name__} class was defined with attribute "
                "'resolve_mutation' but it's not callable"
            )

    @classmethod
    def __bind_to_schema__(cls, schema):
        graphql_type = schema.type_map.get(cls.graphql_name)
        graphql_type.fields[cls.mutation_name].resolve = cls.resolve_mutation

        if cls.__args__:
            field_args = graphql_type.fields[cls.mutation_name].args
            for arg_name, out_name in cls.__args__.items():
                field_args[arg_name].out_name = out_name
