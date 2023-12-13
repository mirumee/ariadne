from graphql import GraphQLSchema

from .enums_values_visitor import (
    GraphQLASTEnumDefaultValueLocation,
    GraphQLASTEnumsValuesVisitor,
    GraphQLSchemaEnumDefaultValueLocation,
    GraphQLSchemaEnumsValuesVisitor,
)


__all__ = [
    "repair_schema_default_enum_values",
    "validate_schema_default_enum_values",
]


def validate_schema_default_enum_values(schema: GraphQLSchema) -> None:
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

    # Example schema with invalid default input field argument

    This schema fails to validate because field `role` on input `UserFilters`
    specifies `REVIEWER` as default value and `REVIEWER` is not a member of
    the `UserRole` enum:

    ```graphql
    type Query {
        field(arg: Input = {field: {field: INVALID}}): String
    }

    input Input {
        field: ChildInput
    }

    input ChildInput {
        field: Role
    }

    enum Role {
        USER
        ADMIN
    }
    ```
    """
    GraphQLEnumsValuesValidatorVisitor(schema)


class GraphQLEnumsValuesValidatorVisitor(GraphQLASTEnumsValuesVisitor):
    def visit_ast_enum_default_value(
        self, location: "GraphQLASTEnumDefaultValueLocation"
    ):
        valid_values = self.enum_values[location.enum_name]
        if location.enum_value not in valid_values:
            if location.arg_name:
                raise ValueError(
                    f"Undefined enum value '{location.enum_value}' for enum "
                    f"'{location.enum_name}' in a default value of "
                    f"'{location.arg_name}' argument for '{location.field_name}' "
                    f"field on '{location.object_name}' type."
                )

            raise ValueError(
                f"Undefined enum value '{location.enum_value}' for enum "
                f"'{location.enum_name}' in a default value of "
                f"'{location.field_name}' field on '{location.object_name}' type."
            )


def repair_schema_default_enum_values(schema: GraphQLSchema) -> None:
    GraphQLSchemaEnumsValuesRepairVisitor(schema)


class GraphQLSchemaEnumsValuesRepairVisitor(GraphQLSchemaEnumsValuesVisitor):
    def visit_schema_enum_default_value(
        self, location: "GraphQLSchemaEnumDefaultValueLocation"
    ):
        valid_values = self.enum_values[location.enum_name]
        valid_default = valid_values[location.enum_value]
        if location.default_value_path is not None:
            location.default_value[location.default_value_path] = valid_default
        elif location.arg_def:
            location.arg_def.default_value = valid_default
        elif location.field_def:
            location.field_def.default_value = valid_default
