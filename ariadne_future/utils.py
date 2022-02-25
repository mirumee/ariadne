from typing import Any

from graphql import DefinitionNode, ListTypeNode, NonNullTypeNode, TypeNode, parse


def parse_definition(type_name: str, schema: Any) -> DefinitionNode:
    if not schema:
        raise TypeError(
            f"{type_name} class was defined without required __schema__ attribute"
        )

    if not isinstance(schema, str):
        raise TypeError(
            f"{type_name} class was defined with __schema__ of invalid type: "
            f"{type(schema).__name__}"
        )

    definitions = parse(schema).definitions

    if len(definitions) > 1:
        definitions_types = [type(definition).__name__ for definition in definitions]
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing more "
            f"than one GraphQL definition (found: {', '.join(definitions_types)})"
        )

    return definitions[0]


def unwrap_type_node(field_type: TypeNode):
    if isinstance(field_type, (NonNullTypeNode, ListTypeNode)):
        return unwrap_type_node(field_type.type)
    return field_type