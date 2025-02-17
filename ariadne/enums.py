import enum
import warnings
from typing import (
    Any,
    Optional,
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
        },
    )
    ```
    """

    def __init__(
        self,
        name: str,
        values: Union[dict[str, Any], type[enum.Enum], type[enum.IntEnum]],
    ) -> None:
        """Initializes the `EnumType` with `name` and `values` mapping.

        # Required arguments

        `name`: a `str` with the name of GraphQL enum type in GraphQL schema to
        bind to.

        `values`: a `dict` or `enums.Enum` with values to use to represent GraphQL
        enum's in Python logic.
        """
        self.name = name
        self.values = cast(dict[str, Any], getattr(values, "__members__", values))

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `EnumType` instance to the instance of GraphQL schema."""
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        graphql_type = cast(GraphQLEnumType, graphql_type)

        for key, value in self.values.items():
            if key not in graphql_type.values:
                raise ValueError(f"Value {key} is not defined on enum {self.name}")
            graphql_type.values[key].value = value

    def bind_to_default_values(self, _schema: GraphQLSchema) -> None:
        """Populates default values of input fields and args in the GraphQL schema.

        This step is required because GraphQL query executor doesn't perform a
        lookup for default values defined in schema. Instead it simply pulls the
        value from fields and arguments `default_value` attribute, which is
        `None` by default.

        > **Deprecated:** Ariadne versions before 0.22 used
        `EnumType.bind_to_default_values` method to fix default enum values embedded
        in the GraphQL schema. Ariadne 0.22 release introduces universal
        `repair_schema_default_enum_values` utility in its place.
        """

        warnings.warn(
            (
                "'EnumType.bind_to_default_values' was deprecated in Ariadne 0.22 and "
                "will be removed in a future release."
            ),
            DeprecationWarning,
        )

    def validate_graphql_type(self, graphql_type: Optional[GraphQLNamedType]) -> None:
        """Validates that schema's GraphQL type associated with this `EnumType`
        is an `enum`."""
        if not graphql_type:
            raise ValueError(f"Enum {self.name} is not defined in the schema")
        if not isinstance(graphql_type, GraphQLEnumType):
            raise ValueError(
                f"{self.name} is defined in the schema, but it is instance of "
                f"{type(graphql_type).__name__} (expected {GraphQLEnumType.__name__})"
            )
