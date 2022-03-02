from typing import Type, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLTypeResolver,
    GraphQLSchema,
    GraphQLUnionType,
    UnionTypeDefinitionNode,
    UnionTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_union_type
from .types import RequirementsDict
from .utils import parse_definition

UnionNodeType = Union[UnionTypeDefinitionNode, UnionTypeExtensionNode]


class UnionType(BaseType):
    __abstract__ = True

    graphql_type: Union[Type[UnionTypeDefinitionNode], Type[UnionTypeExtensionNode]]
    resolve_type: GraphQLTypeResolver

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

        dependencies = cls.__get_dependencies__(graphql_def)
        cls.__validate_requirements__(requirements, dependencies)

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> UnionNodeType:
        if not isinstance(type_def, (UnionTypeDefinitionNode, UnionTypeExtensionNode)):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ "
                "without GraphQL union"
            )

        return cast(UnionNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: UnionNodeType, requirements: RequirementsDict
    ):
        if not isinstance(type_def, UnionTypeExtensionNode):
            return

        graphql_name = type_def.name.value
        if graphql_name not in requirements:
            raise ValueError(
                f"{cls.__name__} class was defined without required GraphQL union "
                f"definition for '{graphql_name}' in __requires__"
            )

        if requirements[graphql_name] != UnionTypeDefinitionNode:
            raise ValueError(
                f"{cls.__name__} requires '{graphql_name}' to be GraphQL union "
                f"but other type was provided in '__requires__'"
            )

    @classmethod
    def __get_dependencies__(cls, type_def: UnionNodeType) -> Dependencies:
        return get_dependencies_from_union_type(type_def)

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        graphql_type = cast(GraphQLUnionType, schema.type_map.get(cls.graphql_name))
        graphql_type.resolve_type = cls.resolve_type
