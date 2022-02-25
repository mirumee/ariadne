from typing import Tuple, Union, Set

from graphql import (
    ConstDirectiveNode,
    FieldDefinitionNode,
    InterfaceTypeDefinitionNode,
    NamedTypeNode,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
)

from .utils import unwrap_type_node

GRAPHQL_TYPES = ("ID", "Int", "String", "Boolean")

Dependencies = Tuple[str, ...]


def extract_dependencies_from_object_type(
    graphql_type: Union[
        InterfaceTypeDefinitionNode,
        ObjectTypeDefinitionNode,
        ObjectTypeExtensionNode,
    ]
) -> Dependencies:
    dependencies: Set[str] = set()
    dependencies.update(
        extract_dependencies_from_directives(graphql_type.directives),
        extract_dependencies_from_fields(graphql_type.fields),
        extract_dependencies_from_interfaces(graphql_type.interfaces),
    )

    if graphql_type.name.value in dependencies:
        # Remove self-dependency
        dependencies.remove(graphql_type.name.value)

    return tuple(dependencies)


def extract_dependencies_from_directives(
    directives: Tuple[ConstDirectiveNode, ...]
) -> Dependencies:
    dependencies: Set[str] = set()
    for directive in directives:
        dependencies.add(directive.name.value)
    return tuple(dependencies)


def extract_dependencies_from_fields(
    fields: Tuple[FieldDefinitionNode, ...]
) -> Dependencies:
    dependencies: Set[str] = set()

    for field_def in fields:
        dependencies.update(extract_dependencies_from_directives(field_def.directives))

        # Get dependency from return type
        field_type = unwrap_type_node(field_def.type)
        if isinstance(field_type, NamedTypeNode):
            field_type_name = field_type.name.value
            if field_type_name not in GRAPHQL_TYPES:
                dependencies.add(field_type_name)

        # Get dependency from arguments
        for arg_def in field_def.arguments:
            dependencies.update(
                extract_dependencies_from_directives(arg_def.directives)
            )

            arg_type = unwrap_type_node(arg_def.type)
            if isinstance(arg_type, NamedTypeNode):
                arg_type_name = arg_type.name.value
                if arg_type_name not in GRAPHQL_TYPES:
                    dependencies.add(arg_type_name)

    return tuple(dependencies)


def extract_dependencies_from_interfaces(
    interfaces: Tuple[NamedTypeNode, ...]
) -> Dependencies:
    dependencies: Set[str] = set()
    for interface in interfaces:
        dependencies.add(interface.name.value)
    return tuple(dependencies)
