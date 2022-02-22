from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from graphql import GraphQLResolveInfo
from graphql.language.ast import (
    DefinitionNode,
    FieldDefinitionNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
    TypeNode,
)

from .base_type import BaseType
from .utils import parse_definition

Dependencies = Tuple[str, ...]
FieldsDict = Dict[str, FieldDefinitionNode]
ObjectNodeType = Union[ObjectTypeDefinitionNode, ObjectTypeExtensionNode]
RequirementsDict = Dict[str, DefinitionNode]

STD_TYPES = ("ID", "Int", "String", "Bool")


class ObjectTypeMeta(type):
    def __new__(cls, name: str, bases, kwargs: dict):
        if kwargs.pop("__abstract__", False):
            # Don't run special logic for ObjectType definition
            return super().__new__(cls, name, bases, kwargs)

        schema = kwargs.get("__schema__")

        graphql_def = assert_valid_type(name, parse_definition(name, schema))
        graphql_fields = extract_graphql_fields(name, graphql_def)

        requirements: RequirementsDict = {
            req.graphql_name: req.graphql_type
            for req in kwargs.setdefault("__requires__", [])
        }

        if isinstance(graphql_def, ObjectTypeExtensionNode):
            validate_base_dependency(name, graphql_def, requirements)

        dependencies = extract_graphql_dependencies(graphql_def)
        validate_fields_dependencies(name, dependencies, requirements)

        kwargs["graphql_name"] = graphql_def.name.value
        kwargs["graphql_type"] = type(graphql_def)

        aliases = kwargs.setdefault("__resolvers__", None)
        defined_resolvers = get_resolvers(kwargs)
        final_resolvers = {}

        for field_name in graphql_fields:
            if aliases and field_name in aliases:
                resolver_name = aliases[field_name]
                if resolver_name in defined_resolvers:
                    final_resolvers[field_name] = defined_resolvers[resolver_name]
                else:
                    final_resolvers[field_name] = create_alias_resolver(resolver_name)

            elif field_name in defined_resolvers:
                final_resolvers[field_name] = defined_resolvers[field_name]

        kwargs["_resolvers"] = final_resolvers

        return super().__new__(cls, name, bases, kwargs)


def extract_graphql_fields(type_name: str, type_def: ObjectNodeType) -> FieldsDict:
    if not type_def.fields:
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing empty "
            f"GraphQL type definition"
        )

    return {field.name.value: field for field in type_def.fields}


def extract_graphql_dependencies(type_def: ObjectNodeType) -> Dependencies:
    dependencies = set()

    for field_def in type_def.fields:
        field_type = unwrap_field_type_node(field_def.type)
        if isinstance(field_type, NamedTypeNode):
            field_type_name = field_type.name.value
            if field_type_name not in STD_TYPES:
                dependencies.add(field_type_name)

    return tuple(dependencies)


def unwrap_field_type_node(field_type: TypeNode):
    if isinstance(field_type, (NonNullTypeNode, ListTypeNode)):
        return unwrap_field_type_node(field_type.type)
    return field_type


def get_resolvers(kwargs: Dict[str, Any]) -> Dict[str, Callable]:
    resolvers = {}
    for name, value in kwargs.items():
        if isinstance(value, staticmethod):
            # Fix for py<3.10
            value = value.__get__(object)

        if not name.startswith("_") and callable(value):
            resolvers[name] = value
    return resolvers


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


def assert_valid_type(type_name: str, type_def: DefinitionNode) -> ObjectNodeType:
    if not isinstance(type_def, (ObjectTypeDefinitionNode, ObjectTypeExtensionNode)):
        raise ValueError(
            f"{type_name} class was defined with __schema__ containing invalid "
            f"GraphQL type definition: {type(type_def).__name__}"
        )

    return cast(ObjectNodeType, type_def)


def validate_base_dependency(
    type_name: str,
    type_def: ObjectTypeExtensionNode,
    requirements: RequirementsDict,
):
    graphql_name = type_def.name.value
    if graphql_name not in requirements:
        raise ValueError(
            f"{type_name} clfgraphql_typeass was defined without required GraphQL type "
            f"definition for '{graphql_name}' in __requires__"
        )


def validate_fields_dependencies(
    type_name: str, dependencies: Dependencies, requirements: RequirementsDict
):
    for graphql_name in dependencies:
        if graphql_name not in requirements:
            raise ValueError(
                f"{type_name} class was defined without required GraphQL type "
                f"definition for '{graphql_name}' in __requires__"
            )


class ObjectType(BaseType, metaclass=ObjectTypeMeta):
    __abstract__ = True
    __root__: Optional[Any]
    __schema__: str
    __resolvers__: Optional[Dict[str, str]]
    __requires__: List[Type[BaseType]]

    graphql_name: str
    graphql_type: ObjectNodeType

    _resolvers: Dict[str, Callable[..., Any]]

    @classmethod
    def __bind_to_schema__(cls, schema):
        graphql_type = schema.type_map.get(cls.graphql_name)

        for field_name, field_resolver in cls._resolvers.items():
            graphql_type.fields[field_name].resolve = field_resolver
