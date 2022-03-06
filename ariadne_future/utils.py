from typing import Any, Dict, Mapping, Optional, Union, cast

from graphql import (
    DefinitionNode,
    GraphQLResolveInfo,
    ListTypeNode,
    NonNullTypeNode,
    TypeNode,
    parse,
)

from ariadne import convert_camel_case_to_snake

from .types import FieldsDict


def parse_definition(type_name: str, schema: Any) -> DefinitionNode:
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


Overrides = Dict[str, str]
ArgsOverrides = Dict[str, Overrides]


def convert_case(
    overrides_or_fields: Optional[Union[FieldsDict, dict]] = None,
    map_fields_args=False,
):
    no_args_call = convert_case_call_without_args(overrides_or_fields)

    overrides = {}
    if not no_args_call:
        overrides = cast(dict, overrides_or_fields)

    def create_case_mappings(fields: FieldsDict, map_fields_args=False):
        if map_fields_args:
            return convert_args_cas(fields, overrides)

        return convert_aliases_case(fields, overrides)

    if no_args_call:
        fields = cast(FieldsDict, overrides_or_fields)
        return create_case_mappings(fields, map_fields_args)

    return create_case_mappings


def convert_case_call_without_args(
    overrides_or_fields: Optional[Union[FieldsDict, dict]] = None
) -> bool:
    if overrides_or_fields is None:
        return True

    if isinstance(list(overrides_or_fields.values())[0], DefinitionNode):
        return True

    return False


def convert_aliases_case(fields: FieldsDict, overrides: Overrides) -> Overrides:
    final_mappings = {}
    for field_name in fields:
        if field_name in overrides:
            field_name_final = overrides[field_name]
        else:
            field_name_final = convert_camel_case_to_snake(field_name)
        if field_name != field_name_final:
            final_mappings[field_name] = field_name_final
    return final_mappings


def convert_args_cas(fields: FieldsDict, overrides: ArgsOverrides) -> ArgsOverrides:
    final_mappings = {}
    for field_name, field_def in fields.items():
        arg_overrides: Overrides = overrides.get(field_name, {})
        arg_mappings = {}
        for arg in field_def.arguments:
            arg_name = arg.name.value
            if arg_name in arg_overrides:
                arg_name_final = arg_overrides[arg_name]
            else:
                arg_name_final = convert_camel_case_to_snake(arg_name)
            if arg_name != arg_name_final:
                arg_mappings[arg_name] = arg_name_final
        if arg_mappings:
            final_mappings[field_name] = arg_mappings
    return final_mappings
