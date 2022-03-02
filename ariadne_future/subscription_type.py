from typing import Callable, Dict, Optional, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLFieldResolver,
    GraphQLObjectType,
    GraphQLSchema,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
)

from .base_type import BaseType
from .dependencies import Dependencies, get_dependencies_from_object_type
from .object_type import create_alias_resolver
from .types import FieldsDict, RequirementsDict
from .utils import parse_definition

ObjectNodeType = Union[ObjectTypeDefinitionNode, ObjectTypeExtensionNode]


class SubscriptionType(BaseType):
    __aliases__: Optional[Dict[str, str]] = None

    resolvers: Dict[str, GraphQLFieldResolver]
    subscribers: Dict[str, GraphQLFieldResolver]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.__dict__.get("__abstract__"):
            return

        graphql_def: ObjectNodeType = cls.__validate_schema__(
            parse_definition(cls.__name__, cls.__schema__)
        )

        cls.graphql_name = graphql_def.name.value
        cls.graphql_type = type(graphql_def)

        graphql_fields = cls.__get_fields__(graphql_def)

        requirements = cls.__get_requirements__()
        if isinstance(graphql_def, ObjectTypeExtensionNode):
            cls.__validate_requirements_contain_extended_type__(
                graphql_def, requirements
            )

        dependencies = cls.__get_dependencies__(graphql_def)
        cls.__validate_requirements__(requirements, dependencies)

        cls.__validate_aliases__(graphql_fields)
        cls.resolvers = cls.__get_resolvers__(graphql_fields)
        cls.subscribers = cls.__get_subscribers__(graphql_fields)

    @classmethod
    def __validate_schema__(cls, type_def: DefinitionNode) -> ObjectNodeType:
        if not isinstance(
            type_def, (ObjectTypeDefinitionNode, ObjectTypeExtensionNode)
        ):
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ without GraphQL type"
            )

        if type_def.name.value != "Subscription":
            raise ValueError(
                f"{cls.__name__} class was defined with __schema__ containing "
                f"GraphQL definition for 'type {type_def.name.value}' "
                "(expected 'type Subscription')"
            )

        return cast(ObjectNodeType, type_def)

    @classmethod
    def __validate_requirements_contain_extended_type__(
        cls, type_def: ObjectNodeType, requirements: RequirementsDict
    ):
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
    def __validate_aliases__(cls, fields: FieldsDict):
        if not cls.__aliases__:
            return

        invalid_aliases = set(cls.__aliases__) - set(fields)
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
    def __get_resolvers__(cls, fields: FieldsDict):
        aliases = cls.__aliases__ or {}
        defined_resolvers = cls.__get_defined_resolvers__()

        used_resolvers = []
        resolvers = {}

        for field_name in fields:
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
    def __get_subscribers__(cls, fields: FieldsDict):
        aliases = cls.__aliases__ or {}
        defined_subscribers = cls.__get_defined_subscribers__()

        used_subscribers = []
        subscribers = {}

        for field_name in fields:
            if aliases and field_name in aliases:
                subscription_name = aliases[field_name]
                if subscription_name in defined_subscribers:
                    used_subscribers.append(subscription_name)
                    subscribers[field_name] = defined_subscribers[subscription_name]

            elif field_name in defined_subscribers:
                used_subscribers.append(field_name)
                subscribers[field_name] = defined_subscribers[field_name]

        unused_subscribers = [
            f"resolve_{field_name}"
            for field_name in set(defined_subscribers) - set(used_subscribers)
        ]
        if unused_subscribers:
            raise ValueError(
                f"{cls.__name__} class was defined with subscribers for fields "
                f"not in  GraphQL type: {', '.join(unused_subscribers)}"
            )

        return subscribers

    @classmethod
    def __get_defined_subscribers__(cls) -> Dict[str, Callable]:
        resolvers = {}
        for name in dir(cls):
            if not name.startswith("subscribe_"):
                continue

            value = getattr(cls, name)
            if callable(value):
                resolvers[name[10:]] = value

        return resolvers

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        graphql_type = cast(GraphQLObjectType, schema.type_map[cls.graphql_name])

        for field_name, field_resolver in cls.resolvers.items():
            graphql_type.fields[field_name].resolve = field_resolver

        for field_name, field_subscriber in cls.subscribers.items():
            graphql_type.fields[field_name].subscribe = field_subscriber
