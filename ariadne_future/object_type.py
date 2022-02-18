from typing import Any, Callable, Dict, List, Optional, Tuple

from graphql import parse
from graphql.language.ast import (
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
    TypeNode,
)


STD_TYPES = ("ID", "Int", "String", "Bool")


class ObjectTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if not bases:
            # Don't run special logic for ObjectType definition
            return super().__new__(cls, name, bases, kwargs)

        root = kwargs.setdefault("__root__", None)
        schema = kwargs.get("__schema__")
        requires = kwargs.setdefault("__requires__", [])
        resolvers = cls.get_resolvers(kwargs)

        type_name, type_extends, type_fields = cls.parse_schema(name, schema)
        kwargs["_graphql_name"] = type_name
        kwargs["_graphql_fields"] = type_fields
        kwargs["_resolvers"] = resolvers

        dependencies = {}
        for requirement in requires:
            dependencies[requirement._graphql_name] = requirement

        if type_extends and type_name not in dependencies:
            raise ValueError(
                f"{name} class was declared with __schema__ extending "
                f"unknown dependency: {type_name}"
            )

        for field_def in type_fields.values():
            field_type = unwrap_field_type_node(field_def.type)
            if isinstance(field_type, NamedTypeNode):
                field_type_name = field_type.name.value
                if (
                    field_type_name not in STD_TYPES
                    and field_type_name not in dependencies
                ):
                    raise ValueError(
                        f"{name} class was declared with __schema__ containing "
                        f"unknown dependency: {field_type_name}"
                    )

        # fields_names = set(type_fields.keys())
        # resolvers_names = set(resolvers.keys())
        # for missing_name in fields_names.symmetric_difference(resolvers_names):
        #     print(missing_name)

        return super().__new__(cls, name, bases, kwargs)

    def get_resolvers(kwargs: Dict[str, Any]) -> Dict[str, Callable]:
        resolvers = {}
        for name, value in kwargs.items():
            if not name.startswith("_") and callable(value):
                resolvers[name] = value
        return resolvers

    def parse_schema(
        name: str, schema: Optional[str]
    ) -> Tuple[str, bool, Dict[str, TypeNode]]:
        if not schema:
            raise TypeError(
                f"{name} class was declared without required __schema__ attribute"
            )

        if not isinstance(schema, str):
            raise TypeError(
                f"{name} class was declared with __schema__ of invalid type: "
                f"{type(schema).__name__}"
            )

        definitions = parse(schema).definitions

        if len(definitions) > 1:
            definitions_types = [
                type(definition).__name__ for definition in definitions
            ]
            raise ValueError(
                f"{name} class was declared with __schema__ containing more "
                f"than one definition (found: {', '.join(definitions_types)})"
            )

        definition = definitions[0]
        type_extends = isinstance(definition, ObjectTypeExtensionNode)

        if not isinstance(
            definition, (ObjectTypeDefinitionNode, ObjectTypeExtensionNode)
        ):
            raise ValueError(
                f"{name} class was declared with __schema__ without GraphQL"
                f" type definition (found: {type(definition).__name__})"
            )

        if not definition.fields:
            raise ValueError(
                f"{name} class was declared with __schema__ containing empty"
                f" GraphQL type definition"
            )

        type_name = definition.name.value
        type_fields = {}

        for field in definition.fields:
            type_fields[field.name.value] = field

        return type_name, type_extends, type_fields


def unwrap_field_type_node(field_type: TypeNode):
    if isinstance(field_type, (NonNullTypeNode, ListTypeNode)):
        return unwrap_field_type_node(field_type.type)
    return field_type


class ObjectType(metaclass=ObjectTypeMeta):
    __root__: Optional[Any]
    __schema__: str
    __resolvers__: Optional[Dict[str, str]]
    __requires__: List["ObjectType"]

    @classmethod
    def __bind_to_schema__(cls, schema):
        graphql_type = schema.type_map.get(cls._graphql_name)

        for field_name, field_resolver in cls._resolvers.items():
            graphql_type.fields[field_name].resolve = field_resolver
