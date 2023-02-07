# pylint: disable=cell-var-from-loop

import re
from inspect import isawaitable
from typing import Any, List

from graphql.language import DirectiveNode
from graphql.type import (
    GraphQLNamedType,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLResolveInfo,
    GraphQLSchema,
)


_i_token_delimiter = r"(?:^|[\s]+|$)"
_i_token_name = "[_A-Za-z][_0-9A-Za-z]*"
_i_token_arguments = r"\([^)]*\)"
_i_token_location = "[_A-Za-z][_0-9A-Za-z]*"
_i_token_description_block_string = r"(?:\"{3}(?:[^\"]{1,}|[\s])\"{3})"
_i_token_description_single_line = r"(?:\"(?:[^\"\n\r])*?\")"

_r_directive_definition = re.compile(
    "("
    f"{_i_token_delimiter}"
    f"(?:{_i_token_description_block_string}|{_i_token_description_single_line})??"
    f"{_i_token_delimiter}directive"
    f"(?:{_i_token_delimiter})?@({_i_token_name})"
    f"(?:(?:{_i_token_delimiter})?{_i_token_arguments})?"
    f"{_i_token_delimiter}on"
    f"{_i_token_delimiter}(?:[|]{_i_token_delimiter})?{_i_token_location}"
    f"(?:{_i_token_delimiter}[|]{_i_token_delimiter}{_i_token_location})*"
    ")"
    f"(?={_i_token_delimiter})",
)

_r_directive = re.compile(
    "("
    f"(?:{_i_token_delimiter})?@({_i_token_name})"
    f"(?:(?:{_i_token_delimiter})?{_i_token_arguments})?"
    ")"
    f"(?={_i_token_delimiter})",
)

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
]


def purge_schema_directives(joined_type_defs: str) -> str:
    """Remove custom schema directives from federation."""
    joined_type_defs = _r_directive_definition.sub("", joined_type_defs)
    joined_type_defs = _r_directive.sub(
        lambda m: m.group(1) if m.group(2) in _allowed_directives else "",
        joined_type_defs,
    )
    return joined_type_defs


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

        resolve_reference = getattr(
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


def get_entity_types(schema: GraphQLSchema) -> List[GraphQLNamedType]:
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
) -> List[DirectiveNode]:
    """Get all directive attached to a type."""
    directives: List[DirectiveNode] = []

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
