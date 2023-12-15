"""Acceptance tests for fixes to some GraphQL enum gotchas.

GraphQL enum members are represented in Python as strings with their names as default.

For example:

enum Role {
    ADMIN
    USER
}

ADMIN in GraphQL schema and queries will be represented as "ADMIN" string in
JSON and Python. This is okay until GraphQL enums are paired to other Python types
using Ariadne's logic.

When either `Enum`, `EnumType` or `GraphQLEnum` is used, Ariadne needs to scan
entire GraphQL schema for places where `default_value` represents enum member,
and replace default string value with valid enum member representation.

Other issue is that standard `validate_schema` is not validating when
`default_value` for field arguments and input fields is a valid enum member.

GitHub issues:

https://github.com/mirumee/ariadne/issues/293
https://github.com/mirumee/ariadne/issues/995
https://github.com/mirumee/ariadne/issues/1074
"""

from enum import Enum

import pytest
from graphql import GraphQLSchema, graphql_sync

from ariadne import EnumType, make_executable_schema


def set_resolver(schema: GraphQLSchema, field: str, resolver):
    schema.type_map["Query"].fields[field].resolve = resolver


def get_arg_type(*_, arg):
    return type(arg).__name__


def get_arg_str(*_, arg):
    return str(arg)


def get_arg_list_type(*_, arg=None):
    return type(arg[0] if arg is not None else None).__name__


def get_arg_list_str(*_, arg=None):
    return str(arg[0] if arg is not None else None)


def get_arg_list_list_type(*_, arg=None):
    return type(arg[0][0] if arg is not None else None).__name__


def get_arg_list_list_str(*_, arg=None):
    return str(arg[0][0] if arg is not None else None)


def get_arg_input_type(*_, arg=None):
    return type(arg.get("role") if arg is not None else None).__name__


def get_arg_input_str(*_, arg=None):
    return str(arg.get("role") if arg is not None else None)


def get_arg_input_list_type(*_, arg=None):
    return type(arg[0].get("role") if arg is not None else None).__name__


def get_arg_input_list_str(*_, arg=None):
    return str(arg[0].get("role") if arg is not None else None)


def get_arg_input_list_def_type(*_, arg=None):
    return type(arg.get("role")[0] if arg is not None else None).__name__


def get_arg_input_list_def_str(*_, arg=None):
    return str(arg.get("role")[0] if arg is not None else None)


def assert_schema_working_defaults(schema: GraphQLSchema):
    """Fail test if GraphQL default values are not Python-representable."""
    result = graphql_sync(
        schema,
        (
            """
            {
                __schema {
                    types {
                        name
                        fields {
                            name
                            args {
                                name
                                defaultValue
                            }
                        }
                        inputFields {
                            name
                            defaultValue
                        }
                    }
                }
            }
            """
        ),
    )

    assert not result.errors


@pytest.fixture
def create_schema():
    def schema_factory(*args):
        schema = make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input NoDef {
                role: Role
            }

            input HasDef {
                role: Role = USER
            }

            input HasListDef {
                role: [Role] = [USER]
            }

            type Query {
                argType(arg: Role): String!
                argValue(arg: Role): String!
                argDefType(arg: Role = USER): String!
                argDefValue(arg: Role = USER): String!
                argDefNull(arg: Role = null): String!
                argListDefType(arg: [Role!] = [USER]): String!
                argListDefValue(arg: [Role!] = [USER]): String!
                argListListDefType(arg: [[Role!]] = [[USER]]): String!
                argListListDefValue(arg: [[Role!]] = [[USER]]): String!
                argInputType(arg: NoDef): String!
                argInputValue(arg: NoDef): String!
                argInputObjType(arg: NoDef = {role: USER}): String!
                argInputObjValue(arg: NoDef = {role: USER}): String!
                argInputListObjType(arg: [NoDef] = [{role: USER}]): String!
                argInputListObjValue(arg: [NoDef] = [{role: USER}]): String!
                argInputDefType(arg: HasDef): String!
                argInputDefValue(arg: HasDef): String!
                argInputDefObjType(arg: HasDef = {}): String!
                argInputDefObjValue(arg: HasDef = {}): String!
                argInputListDefType(arg: HasListDef = {}): String!
                argInputListDefValue(arg: HasListDef = {}): String!
                argInputListDefObjType(arg: HasListDef = {role: [USER]}): String!
                argInputListDefObjValue(arg: HasListDef = {role: [USER]}): String!
                pyStr: Role
                pyInt: Role
                pyEnum: Role
            }
            """,
            *args,
        )

        set_resolver(schema, "argType", get_arg_type)
        set_resolver(schema, "argValue", get_arg_str)
        set_resolver(schema, "argDefType", get_arg_type)
        set_resolver(schema, "argDefValue", get_arg_str)
        set_resolver(schema, "argListDefType", get_arg_list_type)
        set_resolver(schema, "argListDefValue", get_arg_list_str)
        set_resolver(schema, "argListListDefType", get_arg_list_list_type)
        set_resolver(schema, "argListListDefValue", get_arg_list_list_str)
        set_resolver(schema, "argInputType", get_arg_input_type)
        set_resolver(schema, "argInputValue", get_arg_input_str)
        set_resolver(schema, "argInputObjType", get_arg_input_type)
        set_resolver(schema, "argInputObjValue", get_arg_input_str)
        set_resolver(schema, "argInputListObjType", get_arg_input_list_type)
        set_resolver(schema, "argInputListObjValue", get_arg_input_list_str)
        set_resolver(schema, "argInputDefType", get_arg_input_type)
        set_resolver(schema, "argInputDefValue", get_arg_input_str)
        set_resolver(schema, "argInputDefObjType", get_arg_input_type)
        set_resolver(schema, "argInputDefObjValue", get_arg_input_str)
        set_resolver(schema, "argInputListDefType", get_arg_input_list_def_type)
        set_resolver(schema, "argInputListDefValue", get_arg_input_list_def_str)
        set_resolver(schema, "argInputListDefObjType", get_arg_input_list_def_type)
        set_resolver(schema, "argInputListDefObjValue", get_arg_input_list_def_str)

        return schema

    return schema_factory


query = """
    {
        argType(arg: ADMIN)
        argValue(arg: ADMIN)
        argDefType
        argDefValue
        argListDefType
        argListDefValue
        argListListDefType
        argListListDefValue
        argInputType(arg: {role: ADMIN})
        argInputValue(arg: {role: ADMIN})
        argInputObjType
        argInputObjValue
        argInputListObjType
        argInputListObjValue
        argInputDefType
        argInputDefValue
        argInputDefObjType
        argInputDefObjValue
        argInputListDefType
        argInputListDefValue
        argInputListDefObjType
        argInputListDefObjValue
        pyStr
        pyInt
        pyEnum
    }
    """


def test_enum_with_default_member_names(create_schema):
    # If no Python values were provided for enum's members,
    # those enum members will be represented as strings in Python
    schema = create_schema()
    set_resolver(schema, "pyStr", lambda *_: "ADMIN")

    result = graphql_sync(schema, query)
    assert not result.errors
    assert result.data == {
        "argType": "str",
        "argValue": "ADMIN",
        "argDefType": "str",
        "argDefValue": "USER",
        "argListDefType": "str",
        "argListDefValue": "USER",
        "argListListDefType": "str",
        "argListListDefValue": "USER",
        "argInputType": "str",
        "argInputValue": "ADMIN",
        "argInputObjType": "str",
        "argInputObjValue": "USER",
        "argInputListObjType": "str",
        "argInputListObjValue": "USER",
        "argInputDefType": "NoneType",
        "argInputDefValue": "None",
        "argInputDefObjType": "str",
        "argInputDefObjValue": "USER",
        "argInputListDefType": "str",
        "argInputListDefValue": "USER",
        "argInputListDefObjType": "str",
        "argInputListDefObjValue": "USER",
        "pyStr": "ADMIN",
        "pyInt": None,
        "pyEnum": None,
    }

    assert_schema_working_defaults(schema)


def test_enum_with_int_values_from_dict(create_schema):
    schema = create_schema(EnumType("Role", {"USER": 0, "ADMIN": 1}))

    set_resolver(schema, "pyInt", lambda *_: 1)

    result = graphql_sync(schema, query)
    assert not result.errors
    assert result.data == {
        "argType": "int",
        "argValue": "1",
        "argDefType": "int",
        "argDefValue": "0",
        "argListDefType": "int",
        "argListDefValue": "0",
        "argListListDefType": "int",
        "argListListDefValue": "0",
        "argInputType": "int",
        "argInputValue": "1",
        "argInputObjType": "int",
        "argInputObjValue": "0",
        "argInputListObjType": "int",
        "argInputListObjValue": "0",
        "argInputDefType": "NoneType",
        "argInputDefValue": "None",
        "argInputDefObjType": "int",
        "argInputDefObjValue": "0",
        "argInputListDefType": "int",
        "argInputListDefValue": "0",
        "argInputListDefObjType": "int",
        "argInputListDefObjValue": "0",
        "pyStr": None,
        "pyInt": "ADMIN",
        "pyEnum": None,
    }

    assert_schema_working_defaults(schema)


def test_enum_with_int_enum_values(create_schema):
    class Role(int, Enum):
        USER = 0
        ADMIN = 1

    schema = create_schema(Role)

    set_resolver(schema, "pyInt", lambda *_: 1)
    set_resolver(schema, "pyEnum", lambda *_: Role.ADMIN)

    result = graphql_sync(schema, query)
    assert not result.errors
    assert result.data == {
        "argType": "Role",
        "argValue": "Role.ADMIN",
        "argDefType": "Role",
        "argDefValue": "Role.USER",
        "argListDefType": "Role",
        "argListDefValue": "Role.USER",
        "argListListDefType": "Role",
        "argListListDefValue": "Role.USER",
        "argInputType": "Role",
        "argInputValue": "Role.ADMIN",
        "argInputObjType": "Role",
        "argInputObjValue": "Role.USER",
        "argInputListObjType": "Role",
        "argInputListObjValue": "Role.USER",
        "argInputDefType": "NoneType",
        "argInputDefValue": "None",
        "argInputDefObjType": "Role",
        "argInputDefObjValue": "Role.USER",
        "argInputListDefType": "Role",
        "argInputListDefValue": "Role.USER",
        "argInputListDefObjType": "Role",
        "argInputListDefObjValue": "Role.USER",
        "pyStr": None,
        "pyInt": "ADMIN",
        "pyEnum": "ADMIN",
    }

    assert_schema_working_defaults(schema)


def test_enum_with_str_enum_values(create_schema):
    class Role(str, Enum):
        USER = "u"
        ADMIN = "a"

    schema = create_schema(Role)

    set_resolver(schema, "pyStr", lambda *_: "a")
    set_resolver(schema, "pyEnum", lambda *_: Role.ADMIN)

    result = graphql_sync(schema, query)
    assert not result.errors
    assert result.data == {
        "argType": "Role",
        "argValue": "Role.ADMIN",
        "argDefType": "Role",
        "argDefValue": "Role.USER",
        "argListDefType": "Role",
        "argListDefValue": "Role.USER",
        "argListListDefType": "Role",
        "argListListDefValue": "Role.USER",
        "argInputType": "Role",
        "argInputValue": "Role.ADMIN",
        "argInputObjType": "Role",
        "argInputObjValue": "Role.USER",
        "argInputListObjType": "Role",
        "argInputListObjValue": "Role.USER",
        "argInputDefType": "NoneType",
        "argInputDefValue": "None",
        "argInputDefObjType": "Role",
        "argInputDefObjValue": "Role.USER",
        "argInputListDefType": "Role",
        "argInputListDefValue": "Role.USER",
        "argInputListDefObjType": "Role",
        "argInputListDefObjValue": "Role.USER",
        "pyStr": "ADMIN",
        "pyInt": None,
        "pyEnum": "ADMIN",
    }

    assert_schema_working_defaults(schema)


def test_invalid_default_field_arg_enum_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            type Query {
                field(arg: Role = INVALID): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_arg_enum_list_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            type Query {
                field(arg: [Role!] = [USER, INVALID]): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_arg_enum_nested_list_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            type Query {
                field(arg: [[Role!]] = [[USER], [INVALID]]): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_input_field_enum_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input Input {
                field: Role = INVALID
            }

            type Query {
                field(arg: Input): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_input_nested_object_enum_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input Input {
                field: ChildInput = {field: INVALID}
            }

            input ChildInput {
                field: Role
            }

            type Query {
                field(arg: Input): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_input_arg_object_enum_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input Input {
                field: Role
            }

            type Query {
                field(arg: Input = {field: INVALID}): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_input_list_arg_object_enum_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input Input {
                field: Role
            }

            type Query {
                field(arg: [Input!] = [{field: USER}, {field: INVALID}]): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_input_arg_nested_object_enum_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input Input {
                field: ChildInput
            }

            input ChildInput {
                field: Role
            }

            type Query {
                field(arg: Input = {field: {field: INVALID}}): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)


def test_invalid_default_field_input_arg_object_enum_list_value_fails_validation():
    with pytest.raises(ValueError) as exc_info:
        make_executable_schema(
            """
            enum Role {
                USER
                ADMIN
            }

            input Input {
                field: [Role] = [INVALID]
            }

            type Query {
                field(arg: Input! = {}): String
            }
            """
        )

    assert "Undefined enum value" in str(exc_info.value)
