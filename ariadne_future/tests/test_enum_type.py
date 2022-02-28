from enum import Enum

import pytest
from graphql import GraphQLError, graphql_sync

from ariadne import SchemaDirectiveVisitor

from ..directive_type import DirectiveType
from ..executable_schema import make_executable_schema
from ..object_type import ObjectType
from ..enum_type import EnumType


def test_enum_type_raises_error_when_defined_without_schema(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            pass

    snapshot.assert_match(err)


def test_enum_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = True

    snapshot.assert_match(err)


def test_enum_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = "enom UserRole"

    snapshot.assert_match(err)


def test_enum_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = "scalar UserRole"

    snapshot.assert_match(err)


def test_enum_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = """
            enum UserRole {
                USER
                MOD
                ADMIN
            }

            enum Category {
                CATEGORY
                LINK
            }
            """

    snapshot.assert_match(err)


def test_enum_type_extracts_graphql_name():
    class UserRoleEnum(EnumType):
        __schema__ = """
            enum UserRole {
                USER
                MOD
                ADMIN
            }
        """

    assert UserRoleEnum.graphql_name == "UserRole"


def test_enum_type_can_be_extended_with_new_values():
    # pylint: disable=unused-variable
    class UserRoleEnum(EnumType):
        __schema__ = """
            enum UserRole {
                USER
                MOD
                ADMIN
            }
        """

    class ExtendUserRoleEnum(EnumType):
        __schema__ = """
        extend enum UserRole {
            MVP
        }
        """
        __requires__ = [UserRoleEnum]


def test_enum_type_can_be_extended_with_directive():
    # pylint: disable=unused-variable
    class ExampleDirective(DirectiveType):
        __schema__ = "directive @example on ENUM"
        __visitor__ = SchemaDirectiveVisitor

    class UserRoleEnum(EnumType):
        __schema__ = """
            enum UserRole {
                USER
                MOD
                ADMIN
            }
        """

    class ExtendUserRoleEnum(EnumType):
        __schema__ = "extend enum UserRole @example"
        __requires__ = [UserRoleEnum, ExampleDirective]


class BaseQueryType(ObjectType):
    __abstract__ = True
    __schema__ = """
    type Query {
        enumToRepr(enum: UserRole = USER): String!
        reprToEnum: UserRole!
    }
    """
    __aliases__ = {
        "enumToRepr": "enum_repr",
    }

    @staticmethod
    def resolve_enum_repr(*_, enum) -> str:
        return repr(enum)


def make_test_schema(enum_type):
    class QueryType(BaseQueryType):
        __requires__ = [enum_type]

    return make_executable_schema(QueryType)


def test_enum_type_can_be_defined_with_dict_mapping():
    class UserRoleEnum(EnumType):
        __schema__ = """
            enum UserRole {
                USER
                MOD
                ADMIN
            }
        """
        __enum__ = {
            "USER": 0,
            "MOD": 1,
            "ADMIN": 2,
        }

    schema = make_test_schema(UserRoleEnum)

    # Specfied enum value is reversed
    result = graphql_sync(schema, "{ enumToRepr(enum: MOD) }")
    assert result.data["enumToRepr"] == "1"

    # Default enum value is reversed
    result = graphql_sync(schema, "{ enumToRepr }")
    assert result.data["enumToRepr"] == "0"

    # Python value is converted to enum
    result = graphql_sync(schema, "{ reprToEnum }", root_value={"reprToEnum": 2})
    assert result.data["reprToEnum"] == "ADMIN"


def test_enum_type_raises_error_when_dict_mapping_misses_items_from_definition(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = """
                enum UserRole {
                    USER
                    MOD
                    ADMIN
                }
            """
            __enum__ = {
                "USER": 0,
                "MODERATOR": 1,
                "ADMIN": 2,
            }

    snapshot.assert_match(err)


def test_enum_type_raises_error_when_dict_mapping_has_extra_items_not_in_definition(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = """
                enum UserRole {
                    USER
                    MOD
                    ADMIN
                }
            """
            __enum__ = {
                "USER": 0,
                "REVIEW": 1,
                "MOD": 2,
                "ADMIN": 3,
            }

    snapshot.assert_match(err)


def test_enum_type_can_be_defined_with_str_enum_mapping():
    class RoleEnum(str, Enum):
        USER = "user"
        MOD = "moderator"
        ADMIN = "administrator"

    class UserRoleEnum(EnumType):
        __schema__ = """
            enum UserRole {
                USER
                MOD
                ADMIN
            }
        """
        __enum__ = RoleEnum

    schema = make_test_schema(UserRoleEnum)

    # Specfied enum value is reversed
    result = graphql_sync(schema, "{ enumToRepr(enum: MOD) }")
    assert result.data["enumToRepr"] == repr(RoleEnum.MOD)

    # Default enum value is reversed
    result = graphql_sync(schema, "{ enumToRepr }")
    assert result.data["enumToRepr"] == repr(RoleEnum.USER)

    # Python value is converted to enum
    result = graphql_sync(
        schema, "{ reprToEnum }", root_value={"reprToEnum": "administrator"}
    )
    assert result.data["reprToEnum"] == "ADMIN"


def test_enum_type_raises_error_when_enum_mapping_misses_items_from_definition(
    snapshot,
):
    class RoleEnum(str, Enum):
        USER = "user"
        MODERATOR = "moderator"
        ADMIN = "administrator"

    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = """
                enum UserRole {
                    USER
                    MOD
                    ADMIN
                }
            """
            __enum__ = RoleEnum

    snapshot.assert_match(err)


def test_enum_type_raises_error_when_enum_mapping_has_extra_items_not_in_definition(
    snapshot,
):
    class RoleEnum(str, Enum):
        USER = "user"
        REVIEW = "review"
        MOD = "moderator"
        ADMIN = "administrator"

    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserRoleEnum(EnumType):
            __schema__ = """
                enum UserRole {
                    USER
                    MOD
                    ADMIN
                }
            """
            __enum__ = RoleEnum

    snapshot.assert_match(err)
