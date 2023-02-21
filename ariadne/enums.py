import enum
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from functools import reduce, singledispatch
import operator

from graphql.type import GraphQLEnumType, GraphQLNamedType, GraphQLSchema
from graphql.language.ast import (
    EnumValueNode,
    InputValueDefinitionNode,
    ObjectValueNode,
)
from graphql.pyutils.undefined import Undefined
from graphql.type.definition import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLInterfaceType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
)

from .types import SchemaBindable


T = TypeVar("T")
ArgumentWithKeys = Tuple[str, str, GraphQLArgument, Optional[List["str"]]]
InputFieldWithKeys = Tuple[str, str, GraphQLInputField, Optional[List["str"]]]
GraphQLNamedInputType = Union[
    GraphQLScalarType, GraphQLEnumType, GraphQLInputObjectType
]


class EnumType(SchemaBindable):
    """Bindable mapping Python values to enumeration members in a GraphQL schema.

    # Example

    Given following GraphQL enum:

    ```graphql
    enum UserRole {
        MEMBER
        MODERATOR
        ADMIN
    }
    ```

    You can use `EnumType` to map it's members to Python `Enum`:

    ```python
    user_role_type = EnumType(
        "UserRole",
        {
            "MEMBER": 0,
            "MODERATOR": 1,
            "ADMIN": 2,
        }
    )
    ```

    `EnumType` also works with dictionaries:

    ```python
    user_role_type = EnumType(
        "UserRole",
        {
            "MEMBER": 0,
            "MODERATOR": 1,
            "ADMIN": 2,
        }
    )
    ```
    """

    def __init__(
        self,
        name: str,
        values: Union[Dict[str, Any], Type[enum.Enum], Type[enum.IntEnum]],
    ) -> None:
        """Initializes the `EnumType` with `name` and `values` mapping.

        # Required arguments

        `name`: a `str` with the name of GraphQL enum type in GraphQL schema to
        bind to.

        `values`: a `dict` or `enums.Enum` with values to use to represent GraphQL
        enum's in Python logic.
        """
        self.name = name
        self.values = cast(Dict[str, Any], getattr(values, "__members__", values))

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `EnumType` instance to the instance of GraphQL schema."""
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLEnumType, graphql_type)

        for key, value in self.values.items():
            if key not in graphql_type.values:
                raise ValueError(
                    "Value %s is not defined on enum %s" % (key, self.name)
                )
            graphql_type.values[key].value = value

    def bind_to_default_values(self, schema: GraphQLSchema) -> None:
        """Populates default values of input fields and args in the GraphQL schema.

        This step is required because GraphQL query executor doesn't perform a
        lookup for default values defined in schema. Instead it simply pulls the
        value from fields and arguments `default_value` attribute, which is
        `None` by default.
        """
        for _, _, arg, key_list in find_enum_values_in_schema(schema):
            type_ = resolve_null_type(arg.type)
            type_ = cast(GraphQLNamedInputType, type_)

            if (
                key_list is None
                and arg.default_value in self.values
                and type_.name == self.name
            ):
                type_ = resolve_null_type(arg.type)
                arg.default_value = self.values[arg.default_value]

            elif key_list is not None:
                enum_value = get_value_from_mapping_value(arg.default_value, key_list)
                type_ = cast(GraphQLEnumType, track_type_for_nested(arg, key_list))

                if enum_value in self.values and type_.name == self.name:
                    set_leaf_value_in_mapping(
                        arg.default_value, key_list, self.values[enum_value]
                    )

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        """Validates that schema's GraphQL type associated with this `EnumType`
        is an `enum`."""
        if not graphql_type:
            raise ValueError("Enum %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLEnumType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLEnumType.__name__)
            )


def set_default_enum_values_on_schema(schema: GraphQLSchema):
    """Sets missing Python values for GraphQL enums in schema.

    Recursively scans GraphQL schema for enums and their values. If `value`
    attribute is empty, its populated with with a string of its GraphQL name.

    This string is then used to represent enum's value in Python instead of `None`.

    # Requires arguments

    `schema`: a GraphQL schema to set enums default values in.
    """
    for type_object in schema.type_map.values():
        if isinstance(type_object, GraphQLEnumType):
            set_default_enum_values(type_object)


def set_default_enum_values(graphql_type: GraphQLEnumType):
    for key in graphql_type.values:
        if graphql_type.values[key].value is None:
            graphql_type.values[key].value = key


def validate_schema_enum_values(schema: GraphQLSchema) -> None:
    """Raises `ValueError` if GraphQL schema has input fields or arguments with
    default values that are undefined enum values.

    # Example schema with invalid field argument

    This schema fails to validate because argument `role` on field `users`
    specifies `REVIEWER` as default value and `REVIEWER` is not a member of
    the `UserRole` enum:

    ```graphql
    type Query {
        users(role: UserRole = REVIEWER): [User!]!
    }

    enum UserRole {
        MEMBER
        MODERATOR
        ADMIN
    }

    type User {
        id: ID!
    }
    ```

    # Example schema with invalid input field

    This schema fails to validate because field `role` on input `UserFilters`
    specifies `REVIEWER` as default value and `REVIEWER` is not a member of
    the `UserRole` enum:

    ```graphql
    type Query {
        users(filter: UserFilters): [User!]!
    }

    input UserFilters {
        name: String
        role: UserRole = REVIEWER
    }

    enum UserRole {
        MEMBER
        MODERATOR
        ADMIN
    }

    type User {
        id: ID!
    }
    ```
    """

    for type_name, field_name, arg, _ in find_enum_values_in_schema(schema):
        if is_invalid_enum_value(arg):
            raise ValueError(
                f"Value for type: <{arg.type}> is invalid. "
                f"Check InputField/Arguments for <{field_name}> in <{type_name}> "
                "(Undefined enum value)."
            )


def is_invalid_enum_value(field: Union[GraphQLInputField, GraphQLArgument]) -> bool:
    if field.ast_node is None:
        return False
    return field.default_value is Undefined and field.ast_node.default_value is not None


def find_enum_values_in_schema(
    schema: GraphQLSchema,
) -> Generator[Union[ArgumentWithKeys, InputFieldWithKeys], None, None]:
    for name, type_ in schema.type_map.items():
        result = enum_values_in_types(type_, name)
        if result is not None:
            yield from result


@singledispatch
def enum_values_in_types(
    type_: GraphQLNamedType,  # pylint: disable=unused-argument
    name: str,  # pylint: disable=unused-argument
) -> Optional[Generator[Union[ArgumentWithKeys, InputFieldWithKeys], None, None]]:
    pass


@enum_values_in_types.register(GraphQLObjectType)
@enum_values_in_types.register(GraphQLInterfaceType)
def enum_values_in_object_type(
    type_: Union[GraphQLObjectType, GraphQLInterfaceType],
    field_name: str,
) -> Generator[ArgumentWithKeys, None, None]:
    for field in type_.fields.values():
        yield from enum_values_in_field_args(field_name, field)


@enum_values_in_types.register(GraphQLInputObjectType)
def enum_values_in_input_type(
    type_: GraphQLInputObjectType,
    field_name,
) -> Generator[InputFieldWithKeys, None, None]:
    yield from _get_field_with_keys(field_name, type_.fields.items())


def enum_values_in_field_args(
    field_name: str,
    field: GraphQLField,
) -> Generator[ArgumentWithKeys, None, None]:
    args = [
        (name, arg)
        for name, arg in field.args.items()
        if isinstance(
            arg.type, (GraphQLInputObjectType, GraphQLEnumType, GraphQLNonNull)
        )
    ]

    yield from _get_field_with_keys(field_name, args)


def _get_field_with_keys(field_name, fields):
    for input_name, field in fields:
        resolved_type = resolve_null_type(field.type)
        if isinstance(resolved_type, GraphQLEnumType):
            yield field_name, input_name, field, None

        if isinstance(resolved_type, GraphQLInputObjectType):
            if field.ast_node is not None and field.ast_node.default_value is not None:
                routes = get_enum_keys_from_ast(field.ast_node)
                for route in routes:
                    yield field_name, input_name, field, route


def get_enum_keys_from_ast(ast_node: InputValueDefinitionNode) -> List[List["str"]]:
    routes = []
    object_node = cast(ObjectValueNode, ast_node.default_value)
    nodes = [([field.name.value], field) for field in object_node.fields]

    while nodes:
        key_list, field = nodes.pop()
        if isinstance(field.value, EnumValueNode):
            routes.append(key_list)

        if isinstance(field.value, ObjectValueNode):
            for new_field in field.value.fields:
                new_route = key_list[:]
                new_route.append(new_field.name.value)
                nodes.append((new_route, new_field))

    return routes


def get_value_from_mapping_value(mapping: Mapping[T, Any], key_list: List[T]) -> Any:
    return reduce(operator.getitem, key_list, mapping)


def set_leaf_value_in_mapping(
    mapping: Mapping[T, Any], key_list: List[T], value: Any
) -> None:
    get_value_from_mapping_value(mapping, key_list[:-1])[key_list[-1]] = value


def track_type_for_nested(
    arg: Union[GraphQLArgument, GraphQLInputField], key_list: List[str]
) -> GraphQLInputType:
    type_ = resolve_null_type(arg.type)

    for elem in key_list:
        if isinstance(type_, GraphQLInputObjectType):
            type_ = type_.fields[elem].type
    return type_


def resolve_null_type(type_: GraphQLInputType) -> GraphQLInputType:
    return type_.of_type if isinstance(type_, GraphQLNonNull) else type_
