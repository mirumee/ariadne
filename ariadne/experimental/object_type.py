from typing import Any, Callable, Dict, List, Optional, Tuple

from graphql import parse
from graphql.language.ast import ObjectTypeDefinitionNode, TypeNode


class ObjectTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if not bases:
            # Don't run special logic for ObjectType definition
            return super().__new__(cls, name, bases, kwargs)

        strict = kwargs.get("__strict__", False)
        root = kwargs.get("__root__", None)
        schema = kwargs.get("__schema__")
        resolvers = cls.get_resolvers(kwargs)

        type_name, type_fields = cls.parse_schema(name, schema)
        kwargs["_graphql_name"] = type_name
        kwargs["_graphql_fields"] = type_fields

        fields_names = set(type_fields.keys())
        resolvers_names = set(resolvers.keys())
        for missing_name in fields_names.symmetric_difference(resolvers_names):
            print(missing_name)

        return super().__new__(cls, name, bases, kwargs)

    def get_resolvers(kwargs: Dict[str, Any]) -> Dict[str, Callable]:
        resolvers = {}
        for name, value in kwargs.items():
            if not name.startswith("_") and callable(value):
                resolvers[name] = value
        return resolvers

    def parse_schema(
        name: str, schema: Optional[str]
    ) -> Tuple[str, Dict[str, TypeNode]]:
        if not schema:
            raise TypeError(
                f"{name} class was declared without required __schema__ attribute"
            )

        if not isinstance(schema, str):
            raise TypeError(
                f"{name} class was declared with __schema__ of invalid type: "
                f"'{type(schema)}'"
            )

        definitions = parse(schema).definitions

        if len(definitions) > 1:
            raise ValueError(
                f"{name} class was declared with __schema__ containing more "
                f"than one definition (found: {len(definitions)})"
            )

        definition = definitions[0]
        if not isinstance(definition, ObjectTypeDefinitionNode):
            raise ValueError(
                f"{name} class was declared with __schema__ without GraphQL"
                f"type definition (found: {type(definition).__name__})"
            )

        type_name = definition.name.value
        type_fields = {}

        for field in definition.fields:
            type_fields[field.name.value] = field.type

        return type_name, type_fields


class ObjectType(metaclass=ObjectTypeMeta):
    __root__: Optional[Any]
    __schema__: str
    __resolvers__: Optional[Dict[str, str]]
    __requires__: List["ObjectType"]
