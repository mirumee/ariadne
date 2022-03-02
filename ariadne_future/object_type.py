from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    Union,
    cast,
)

from graphql import (
    DefinitionNode,
    GraphQLFieldResolver,
    GraphQLResolveInfo,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_object_type
from .types import FieldsDict, RequirementsDict
from .utils import parse_definition

ObjectNodeType = Union[ObjectTypeDefinitionNode, ObjectTypeExtensionNode]


class ObjectType(BaseType):
    __abstract__ = True
    __schema__: str
    __requires__: List[Type[BaseType]]
    __aliases__: Optional[Dict[str, str]] = None
    __args__: Optional[Dict[str, Dict[str, str]]]

    graphql_name: str
    graphql_type: Union[Type[ObjectTypeDefinitionNode], Type[ObjectTypeExtensionNode]]
    graphql_fields: FieldsDict

    resolvers: Dict[str, GraphQLFieldResolver]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.__dict__.get("__abstract__"):
            return

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
    def __validate_aliases__(cls):
        if not cls.__aliases__:
            return

        invalid_aliases = set(cls.__aliases__) - set(cls.graphql_fields)
        if invalid_aliases:
            raise ValueError(
                f"{cls.__name__} class was defined with aliases for fields not in "
                f"GraphQL type: {', '.join(invalid_aliases)}"
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
    def __get_resolvers__(cls):
        aliases = cls.__aliases__ or {}
        defined_resolvers = cls.__get_defined_resolvers__()

        used_resolvers = []
        resolvers = {}

        for field_name in cls.graphql_fields:
            if aliases and field_name in aliases:
                resolver_name = aliases[field_name]
                if resolver_name in defined_resolvers:
                    used_resolvers.append(resolver_name)
                    resolvers[field_name] = defined_resolvers[resolver_name]
                else:
                    resolvers[field_name] = create_alias_resolver(resolver_name)

            elif field_name in defined_resolvers:
                used_resolvers.append(field_name)
                resolvers[field_name] = defined_resolvers[field_name]

        unused_resolvers = [
            f"resolve_{field_name}"
            for field_name in set(defined_resolvers) - set(used_resolvers)
        ]
        if unused_resolvers:
            raise ValueError(
                f"{cls.__name__} class was defined with resolvers for fields not in "
                f"GraphQL type: {', '.join(unused_resolvers)}"
            )

        return resolvers

    @classmethod
    def __get_defined_resolvers__(cls) -> Dict[str, Callable]:
        resolvers = {}
        for name in dir(cls):
            if not name.startswith("resolve_"):
                continue

            value = getattr(cls, name)
            if callable(value):
                resolvers[name[8:]] = value

        return resolvers

    @classmethod
    def __bind_to_schema__(cls, schema):
        graphql_type = schema.type_map.get(cls.graphql_name)

        for field_name, field_resolver in cls.resolvers.items():
            graphql_type.fields[field_name].resolve = field_resolver


def create_alias_resolver(field_name: str):
    def default_aliased_field_resolver(
        source: Any, info: GraphQLResolveInfo, **args: Any
    ) -> Any:
        value = (
            source.get(field_name)
            if isinstance(source, Mapping)
            else getattr(source, field_name, None)
        )

        if callable(value):
            return value(info, **args)
        return value

    return default_aliased_field_resolver
