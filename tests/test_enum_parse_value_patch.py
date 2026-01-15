"""Tests for _patch_enum_parse_value function.

This function patches enum parse_value methods to accept already-converted
Python enum values, which is necessary for compatibility with graphql-core >= 3.2.6
that coerces input object argument defaults during query execution.
"""

import sys
from enum import Enum

import pytest
from graphql import (
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLError,
    build_ast_schema,
    parse,
)

from ariadne.enums_default_values import _patch_enum_parse_value


class StrRole(str, Enum):
    USER = "u"
    ADMIN = "a"


class IntRole(int, Enum):
    USER = 0
    ADMIN = 1


class PlainRole(Enum):
    USER = "user_value"
    ADMIN = "admin_value"


@pytest.fixture
def str_enum_type():
    """Create a GraphQL enum type with str enum values."""
    return GraphQLEnumType(
        "StrRole",
        {
            "USER": GraphQLEnumValue(StrRole.USER),
            "ADMIN": GraphQLEnumValue(StrRole.ADMIN),
        },
    )


@pytest.fixture
def int_enum_type():
    """Create a GraphQL enum type with int enum values."""
    return GraphQLEnumType(
        "IntRole",
        {
            "USER": GraphQLEnumValue(IntRole.USER),
            "ADMIN": GraphQLEnumValue(IntRole.ADMIN),
        },
    )


@pytest.fixture
def plain_enum_type():
    """Create a GraphQL enum type with plain enum values."""
    return GraphQLEnumType(
        "PlainRole",
        {
            "USER": GraphQLEnumValue(PlainRole.USER),
            "ADMIN": GraphQLEnumValue(PlainRole.ADMIN),
        },
    )


@pytest.fixture
def schema_with_enums():
    """Create a schema with multiple enum types."""
    schema_str = """
        enum StrRole {
            USER
            ADMIN
        }

        enum IntRole {
            USER
            ADMIN
        }

        type Query {
            strRole: StrRole
            intRole: IntRole
        }
    """
    schema = build_ast_schema(parse(schema_str))

    # Bind Python enum values
    str_enum = schema.type_map["StrRole"]
    str_enum.values["USER"].value = StrRole.USER
    str_enum.values["ADMIN"].value = StrRole.ADMIN

    int_enum = schema.type_map["IntRole"]
    int_enum.values["USER"].value = IntRole.USER
    int_enum.values["ADMIN"].value = IntRole.ADMIN

    return schema


class TestPatchEnumParseValueWithStrEnum:
    """Tests for _patch_enum_parse_value with str enums."""

    def test_unpatched_parse_value_fails_with_already_converted_value(
        self, str_enum_type
    ):
        """Without patch, parse_value fails when given an already-converted value."""
        with pytest.raises(GraphQLError) as exc_info:
            str_enum_type.parse_value(StrRole.USER)

        if sys.version_info >= (3, 11):
            expected = "Value 'StrRole.USER' does not exist in 'StrRole' enum"
        else:
            expected = "Value 'u' does not exist in 'StrRole' enum"
        assert expected in str(exc_info.value)

    def test_patched_parse_value_accepts_already_converted_value(self, str_enum_type):
        """After patch, parse_value accepts already-converted enum values."""
        # Create a minimal schema to apply the patch
        schema = build_ast_schema(
            parse("enum StrRole { USER ADMIN } type Query { role: StrRole }")
        )
        schema.type_map["StrRole"] = str_enum_type

        _patch_enum_parse_value(schema)

        # Now parse_value should accept already-converted values
        result = str_enum_type.parse_value(StrRole.USER)
        assert result is StrRole.USER

        result = str_enum_type.parse_value(StrRole.ADMIN)
        assert result is StrRole.ADMIN

    def test_patched_parse_value_still_parses_string_keys(self, str_enum_type):
        """After patch, parse_value still correctly parses string enum keys."""
        schema = build_ast_schema(
            parse("enum StrRole { USER ADMIN } type Query { role: StrRole }")
        )
        schema.type_map["StrRole"] = str_enum_type

        _patch_enum_parse_value(schema)

        # String keys should still work
        result = str_enum_type.parse_value("USER")
        assert result is StrRole.USER

        result = str_enum_type.parse_value("ADMIN")
        assert result is StrRole.ADMIN

    def test_patched_parse_value_rejects_invalid_string(self, str_enum_type):
        """After patch, parse_value still rejects invalid string values."""
        schema = build_ast_schema(
            parse("enum StrRole { USER ADMIN } type Query { role: StrRole }")
        )
        schema.type_map["StrRole"] = str_enum_type

        _patch_enum_parse_value(schema)

        with pytest.raises(GraphQLError) as exc_info:
            str_enum_type.parse_value("INVALID")

        assert "does not exist in 'StrRole' enum" in str(exc_info.value)


class TestPatchEnumParseValueWithIntEnum:
    """Tests for _patch_enum_parse_value with int enums."""

    def test_unpatched_parse_value_fails_with_already_converted_value(
        self, int_enum_type
    ):
        """Without patch, parse_value fails when given an already-converted int enum."""
        with pytest.raises(GraphQLError) as exc_info:
            int_enum_type.parse_value(IntRole.USER)

        assert "cannot represent non-string value" in str(exc_info.value)

    def test_patched_parse_value_accepts_already_converted_value(self, int_enum_type):
        """After patch, parse_value accepts already-converted int enum values."""
        schema = build_ast_schema(
            parse("enum IntRole { USER ADMIN } type Query { role: IntRole }")
        )
        schema.type_map["IntRole"] = int_enum_type

        _patch_enum_parse_value(schema)

        result = int_enum_type.parse_value(IntRole.USER)
        assert result is IntRole.USER

        result = int_enum_type.parse_value(IntRole.ADMIN)
        assert result is IntRole.ADMIN

    def test_patched_parse_value_still_parses_string_keys(self, int_enum_type):
        """After patch, parse_value still correctly parses string enum keys."""
        schema = build_ast_schema(
            parse("enum IntRole { USER ADMIN } type Query { role: IntRole }")
        )
        schema.type_map["IntRole"] = int_enum_type

        _patch_enum_parse_value(schema)

        result = int_enum_type.parse_value("USER")
        assert result is IntRole.USER

        result = int_enum_type.parse_value("ADMIN")
        assert result is IntRole.ADMIN


class TestPatchEnumParseValueWithPlainEnum:
    """Tests for _patch_enum_parse_value with plain (non-mixin) enums."""

    def test_patched_parse_value_accepts_already_converted_value(self, plain_enum_type):
        """After patch, parse_value accepts already-converted plain enum values."""
        schema = build_ast_schema(
            parse("enum PlainRole { USER ADMIN } type Query { role: PlainRole }")
        )
        schema.type_map["PlainRole"] = plain_enum_type

        _patch_enum_parse_value(schema)

        result = plain_enum_type.parse_value(PlainRole.USER)
        assert result is PlainRole.USER

        result = plain_enum_type.parse_value(PlainRole.ADMIN)
        assert result is PlainRole.ADMIN

    def test_patched_parse_value_still_parses_string_keys(self, plain_enum_type):
        """After patch, parse_value still correctly parses string enum keys."""
        schema = build_ast_schema(
            parse("enum PlainRole { USER ADMIN } type Query { role: PlainRole }")
        )
        schema.type_map["PlainRole"] = plain_enum_type

        _patch_enum_parse_value(schema)

        result = plain_enum_type.parse_value("USER")
        assert result is PlainRole.USER

        result = plain_enum_type.parse_value("ADMIN")
        assert result is PlainRole.ADMIN


class TestPatchEnumParseValueAppliedToAllEnums:
    """Tests that the patch is applied to all enum types in the schema."""

    def test_patch_applied_to_all_enum_types(self, schema_with_enums):
        """The patch should be applied to all enum types in the schema."""
        _patch_enum_parse_value(schema_with_enums)

        str_enum = schema_with_enums.type_map["StrRole"]
        int_enum = schema_with_enums.type_map["IntRole"]

        # Both enums should accept already-converted values
        assert str_enum.parse_value(StrRole.USER) is StrRole.USER
        assert int_enum.parse_value(IntRole.USER) is IntRole.USER

        # Both should still parse string keys
        assert str_enum.parse_value("ADMIN") is StrRole.ADMIN
        assert int_enum.parse_value("ADMIN") is IntRole.ADMIN

    def test_introspection_types_are_also_patched(self, schema_with_enums):
        """Introspection enum types are also patched (which is harmless)."""
        _patch_enum_parse_value(schema_with_enums)

        # Introspection enums like __TypeKind use Python enums internally.
        # The patch makes them accept both string keys and Python enum values.
        type_kind_enum = schema_with_enums.type_map.get("__TypeKind")
        if type_kind_enum:
            from graphql import TypeKind

            # Should accept string key
            result = type_kind_enum.parse_value("SCALAR")
            assert result == TypeKind.SCALAR

            # Should also accept already-converted Python enum value
            result = type_kind_enum.parse_value(TypeKind.SCALAR)
            assert result == TypeKind.SCALAR


class TestPatchEnumParseValueEdgeCases:
    """Edge case tests for _patch_enum_parse_value."""

    def test_enum_with_none_value(self):
        """Test enum where a member has None as its value."""
        enum_type = GraphQLEnumType(
            "NullableRole",
            {
                "NONE": GraphQLEnumValue(None),
                "USER": GraphQLEnumValue("user"),
            },
        )

        schema = build_ast_schema(
            parse("enum NullableRole { NONE USER } type Query { role: NullableRole }")
        )
        schema.type_map["NullableRole"] = enum_type

        _patch_enum_parse_value(schema)

        # String keys should still work
        assert enum_type.parse_value("USER") == "user"
        # None value - the original parse_value handles this

    def test_enum_with_duplicate_values(self):
        """Test enum where multiple members have the same value."""

        class DuplicateRole(str, Enum):
            ADMIN = "admin"
            SUPERUSER = "admin"  # Same value as ADMIN

        enum_type = GraphQLEnumType(
            "DuplicateRole",
            {
                "ADMIN": GraphQLEnumValue(DuplicateRole.ADMIN),
                "SUPERUSER": GraphQLEnumValue(DuplicateRole.SUPERUSER),
            },
        )

        schema = build_ast_schema(
            parse(
                "enum DuplicateRole { ADMIN SUPERUSER } "
                "type Query { role: DuplicateRole }"
            )
        )
        schema.type_map["DuplicateRole"] = enum_type

        _patch_enum_parse_value(schema)

        # Both should be recognized as already-converted
        # Note: DuplicateRole.SUPERUSER is DuplicateRole.ADMIN due to enum aliasing
        assert enum_type.parse_value(DuplicateRole.ADMIN) is DuplicateRole.ADMIN

    def test_multiple_patch_calls_are_safe(self, str_enum_type):
        """Calling _patch_enum_parse_value multiple times should be safe."""
        schema = build_ast_schema(
            parse("enum StrRole { USER ADMIN } type Query { role: StrRole }")
        )
        schema.type_map["StrRole"] = str_enum_type

        # Patch multiple times
        _patch_enum_parse_value(schema)
        _patch_enum_parse_value(schema)
        _patch_enum_parse_value(schema)

        # Should still work correctly
        assert str_enum_type.parse_value(StrRole.USER) is StrRole.USER
        assert str_enum_type.parse_value("ADMIN") is StrRole.ADMIN
