from inspect import isawaitable
from typing import Any, cast

from graphql import (
    DirectiveDefinitionNode,
    Node,
    parse,
    print_ast,
)
from graphql.language import DirectiveNode
from graphql.type import (
    GraphQLInputObjectType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLSchema,
)

from ariadne.utils import type_get_extension

_allowed_directives = [
    "skip",  # Default directive as per specs.
    "include",  # Default directive as per specs.
    "deprecated",  # Default directive as per specs.
    "external",  # Federation directive.
    "requires",  # Federation directive.
    "provides",  # Federation directive.
    "key",  # Federation directive.
    "extends",  # Federation directive.
    "link",  # Federation 2 directive.
    "shareable",  # Federation 2 directive.
    "tag",  # Federation 2 directive.
    "override",  # Federation 2 directive.
    "inaccessible",  # Federation 2 directive.
    "composeDirective",  # Federation 2.1 directive.
    "interfaceObject",  # Federation 2.3 directive.
    "authenticated",  # Federation 2.5 directive.
    "requiresScopes",  # Federation 2.5 directive.
    "policy",  # Federation 2.6 directive.
]


def _purge_directive_nodes(nodes: tuple[Node, ...]) -> tuple[Node, ...]:
    return tuple(
        node
        for node in nodes
        if not isinstance(node, (DirectiveNode, DirectiveDefinitionNode))
        or node.name.value in _allowed_directives
    )


def _purge_type_directives(definition: Node):
    # Recursively check every field defined on the Node definition
    # and remove any directives found.
    for key in definition.keys:
        value = getattr(definition, key, None)
        if isinstance(value, tuple):
            # Remove directive nodes from the tuple
            # e.g. doc -> definitions [DirectiveDefinitionNode]
            next_value = _purge_directive_nodes(cast(tuple[Node, ...], value))
            for item in next_value:
                if isinstance(item, Node):
                    # Look for directive nodes on sub-nodes, e.g.: doc ->
                    # definitions [ObjectTypeDefinitionNode] -> fields -> directives
                    _purge_type_directives(item)
            setattr(definition, key, next_value)
        elif isinstance(value, Node):
            _purge_type_directives(value)


def purge_schema_directives(joined_type_defs: str) -> str:
    """Remove custom schema directives from federation."""
    ast_document = parse(joined_type_defs)
    _purge_type_directives(ast_document)
    return print_ast(ast_document)


def resolve_entities(_: Any, info: GraphQLResolveInfo, **kwargs) -> Any:
    representations = list(kwargs.get("representations", []))

    result = []
    for reference in representations:
        __typename = reference["__typename"]
        type_object = info.schema.get_type(__typename)

        if not type_object or not isinstance(type_object, GraphQLObjectType):
            raise TypeError(
                f"The `_entities` resolver tried to load an entity for"
                f' type "{__typename}", but no object type of that name'
                f" was found in the schema",
            )

        resolve_reference = type_get_extension(
            type_object,
            "__resolve_reference__",
            lambda o, i, r: reference,
        )

        representation = resolve_reference(type_object, info, reference)

        if isawaitable(representation):
            result.append(add_typename_to_async_return(representation, __typename))
        else:
            result.append(add_typename_to_possible_return(representation, __typename))

    return result


async def add_typename_to_async_return(obj: Any, typename: str) -> Any:
    return add_typename_to_possible_return(await obj, typename)


def get_entity_types(schema: GraphQLSchema) -> list[GraphQLNamedType]:
    """Get all types that include the @key directive."""
    schema_types = schema.type_map.values()

    def check_type(t):
        return isinstance(t, GraphQLObjectType) and includes_directive(t, "key")

    return [t for t in schema_types if check_type(t)]


def includes_directive(
    type_object: GraphQLNamedType,
    directive_name: str,
) -> bool:
    """Check if specified type includes a directive."""
    if isinstance(type_object, GraphQLInputObjectType):
        return False

    directives = gather_directives(type_object)
    return any(d.name.value == directive_name for d in directives)


def gather_directives(
    type_object: GraphQLNamedType,
) -> list[DirectiveNode]:
    """Get all directive attached to a type."""
    directives: list[DirectiveNode] = []

    if hasattr(type_object, "extension_ast_nodes") and type_object.extension_ast_nodes:
        for ast_node in type_object.extension_ast_nodes:
            if ast_node.directives:
                directives.extend(ast_node.directives)

    if (
        hasattr(type_object, "ast_node")
        and type_object.ast_node
        and type_object.ast_node.directives
    ):
        directives.extend(type_object.ast_node.directives)

    return directives


def add_typename_to_possible_return(obj: Any, typename: str) -> Any:
    if obj is not None:
        if isinstance(obj, dict):
            obj["__typename"] = typename
        else:
            setattr(obj, f"_{obj.__class__.__name__}__typename", typename)
        return obj
    return None
