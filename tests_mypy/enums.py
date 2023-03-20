from enum import Enum, IntEnum

from ariadne import EnumType, make_executable_schema


class TestEnum(Enum):
    FOO = "foo"
    BAR = "bar"


class TestIntEnum(IntEnum):
    FOO = 0
    BAR = 1


test_dict_enum_type = EnumType("TestDictEnum", {"FOO": "foo", "BAR": "bar"})
test_enum_type = EnumType("TestEnum", TestEnum)
test_int_enum_type = EnumType("TestIntEnumType", TestIntEnum)


make_executable_schema(
    """
    type Query {
        test: TestEnum!
    }

    enum TestEnum {
        FOO
        VAR
    }
    """,
    TestEnum,
)
