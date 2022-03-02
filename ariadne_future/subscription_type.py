from typing import Callable, Dict, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLFieldResolver,
    GraphQLObjectType,
    GraphQLSchema,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
)

from .object_type import ObjectType

ObjectNodeType = Union[ObjectTypeDefinitionNode, ObjectTypeExtensionNode]


class SubscriptionType(ObjectType):
    __abstract__ = True

    subscribers: Dict[str, GraphQLFieldResolver]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls.__dict__.get("__abstract__"):
            return

        cls.subscribers = cls.__get_subscribers__()

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
    def __get_subscribers__(cls):
        aliases = cls.__aliases__ or {}
        defined_subscribers = cls.__get_defined_subscribers__()

        used_subscribers = []
        subscribers = {}

        for field_name in cls.graphql_fields:
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
