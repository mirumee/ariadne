import enum
from typing import (
    Any,
    Dict,
    Optional,
    Type,
    Union,
    cast,
)

from graphql.type import GraphQLEnumType, GraphQLNamedType, GraphQLSchema

from .types import SchemaBindable


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
        raise NotImplementedError("DON'T USE bind_to_default_values")
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
