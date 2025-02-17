from enum import Enum, IntEnum

import pytest
from graphql import build_schema, graphql_sync

from ariadne import EnumType, QueryType, make_executable_schema

enum_definition = """
    enum Episode {
        NEWHOPE
        EMPIRE
        JEDI
    }
"""

enum_field = """
    type Query {
        testEnum: Episode!
    }
"""


def test_succesfull_enum_typed_field():
    query = QueryType()
    query.set_field("testEnum", lambda *_: "NEWHOPE")

    schema = make_executable_schema([enum_definition, enum_field], query)
    result = graphql_sync(schema, "{ testEnum }")
    assert result.errors is None
    assert result.data == {"testEnum": "NEWHOPE"}


def test_unsuccesfull_invalid_enum_value_evaluation():
    query = QueryType()
    query.set_field("testEnum", lambda *_: "INVALID")

    schema = make_executable_schema([enum_definition, enum_field], query)
    result = graphql_sync(schema, "{ testEnum }")
    assert result.errors is not None


enum_param = """
    type Query {
        testEnum(value: Episode!): Boolean!
    }
"""


def test_successful_enum_value_passed_as_argument():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: True)

    schema = make_executable_schema([enum_definition, enum_param], query)
    result = graphql_sync(schema, "{{ testEnum(value: {}) }}".format("NEWHOPE"))
    assert result.errors is None, result.errors


def test_unbound_enum_arg_is_transformed_to_string():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: value == "NEWHOPE")

    schema = make_executable_schema([enum_definition, enum_param], [query])
    result = graphql_sync(schema, "{ testEnum(value: NEWHOPE) }")
    assert result.data["testEnum"] is True

    result = graphql_sync(schema, "{ testEnum(value: EMPIRE) }")
    assert result.data["testEnum"] is False


def test_unsuccessful_invalid_enum_value_passed_as_argument():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: True)

    schema = make_executable_schema([enum_definition, enum_param], query)
    result = graphql_sync(schema, "{{ testEnum(value: {}) }}".format("INVALID"))
    assert result.errors is not None


@pytest.fixture
def schema_with_enum():
    return build_schema("\n\n".join((enum_definition, enum_field)))


def test_attempt_bind_custom_enum_to_undefined_type_raises_error(schema_with_enum):
    graphql_enum = EnumType("Undefined", {})
    with pytest.raises(ValueError):
        graphql_enum.bind_to_schema(schema_with_enum)


def test_attempt_bind_custom_enum_to_wrong_schema_type_raises_error(schema_with_enum):
    graphql_enum = EnumType("Query", {})
    with pytest.raises(ValueError):
        graphql_enum.bind_to_schema(schema_with_enum)


def test_attempt_bind_custom_enum_to_schema_enum_missing_value_raises_error(
    schema_with_enum,
):
    graphql_enum = EnumType("Episode", {"JARJAR": 1999})
    with pytest.raises(ValueError):
        graphql_enum.bind_to_schema(schema_with_enum)


dict_enum = EnumType("Episode", {"NEWHOPE": 1977, "EMPIRE": 1980, "JEDI": 1983})


def test_dict_enum_is_resolved_from_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_: 1977)

    schema = make_executable_schema([enum_definition, enum_field], [query, dict_enum])
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "NEWHOPE"


def test_dict_enum_arg_is_transformed_to_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: value == 1977)

    schema = make_executable_schema([enum_definition, enum_param], [query, dict_enum])
    result = graphql_sync(schema, "{{ testEnum(value: {}) }}".format("NEWHOPE"))
    assert result.data["testEnum"] is True


class PyEnum(Enum):
    NEWHOPE = "new-hope"
    EMPIRE = "empire-strikes"
    JEDI = "return-jedi"


py_enum = EnumType("Episode", PyEnum)


def test_enum_is_resolved_from_member_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_: PyEnum.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_field], [query, py_enum])
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "NEWHOPE"


def test_enum_arg_is_transformed_to_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: value == PyEnum.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_param], [query, py_enum])
    result = graphql_sync(schema, "{ testEnum(value: NEWHOPE) }")
    assert result.data["testEnum"] is True


class PyStrEnum(str, Enum):
    NEWHOPE = "new-hope"
    EMPIRE = "empire-strikes"
    JEDI = "return-jedi"


py_str_enum = EnumType("Episode", PyStrEnum)


def test_str_enum_is_resolved_from_member_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_: PyStrEnum.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_field], [query, py_str_enum])
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "NEWHOPE"


def test_str_enum_is_resolved_from_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_: "empire-strikes")

    schema = make_executable_schema([enum_definition, enum_field], [query, py_str_enum])
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "EMPIRE"


def test_str_enum_arg_is_transformed_to_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: value == PyStrEnum.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_param], [query, py_str_enum])
    result = graphql_sync(schema, "{ testEnum(value: NEWHOPE) }")
    assert result.data["testEnum"] is True


class PyIntEnum(IntEnum):
    NEWHOPE = 1977
    EMPIRE = 1980
    JEDI = 1983


int_enum = EnumType("Episode", PyIntEnum)


def test_int_enum_is_resolved_from_field_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_: PyIntEnum.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_field], [query, int_enum])
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "NEWHOPE"


def test_int_enum_is_resolved_from_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_: 1980)

    schema = make_executable_schema([enum_definition, enum_field], [query, int_enum])
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "EMPIRE"


def test_int_enum_arg_is_transformed_to_internal_value():
    query = QueryType()
    query.set_field("testEnum", lambda *_, value: value == PyIntEnum.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_param], [query, int_enum])
    result = graphql_sync(schema, "{ testEnum(value: NEWHOPE) }")
    assert result.data["testEnum"] is True


def test_int_enum_arg_default_python_value_is_set():
    enum_param_default = """
       type Query {
           testEnum(value: Episode! = EMPIRE): Boolean!
       }
    """
    query = QueryType()

    def resolve_test_enum(*_, value):
        return value == PyIntEnum.EMPIRE

    query.set_field("testEnum", resolve_test_enum)
    schema = make_executable_schema(
        [enum_definition, enum_param_default], [query, int_enum]
    )
    result = graphql_sync(schema, "{ testEnum }")

    assert result.data["testEnum"]
    assert result.errors is None


def test_int_enum_input_default_python_value_is_set():
    input_param_default = """
        type Query {
            testEnum(inp: QueryInput): Boolean!
        }
         input QueryInput {
            value: Episode! = EMPIRE
        }
    """
    query = QueryType()

    def resolve_test_enum(*_, inp):
        return inp["value"] == PyIntEnum.EMPIRE

    query.set_field("testEnum", resolve_test_enum)
    schema = make_executable_schema(
        [enum_definition, input_param_default], [query, int_enum]
    )
    result = graphql_sync(schema, "{ testEnum(inp: {}) }")

    assert result.errors is None
    assert result.data["testEnum"]


def test_int_enum_input_nested_default_python_value_is_set():
    input_schema = """
        type Query {
            complex(i: BetterTest = { test: { role: EMPIRE }}): Boolean 
        }
        input Test {
            ignore: String 
            role: Episode = EMPIRE  
        }
        input BetterTest {
            newIgnore: String
            test: Test = { role: NEWHOPE }
        }
    """
    query = QueryType()

    def resolve_test_enum(*_, i):
        return i["test"]["role"] == PyIntEnum.EMPIRE

    query.set_field("complex", resolve_test_enum)
    schema = make_executable_schema([enum_definition, input_schema], [query, int_enum])
    result = graphql_sync(schema, "{ complex(i: {test: {} }) }")

    assert result.errors is None
    assert result.data["complex"]


def test_python_enums_can_be_passed_directly_to_make_executable_schema():
    class Episode(Enum):
        NEWHOPE = "new-hope"
        EMPIRE = "empire-strikes"
        JEDI = "return-jedi"

    query = QueryType()
    query.set_field("testEnum", lambda *_: Episode.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_field], query, Episode)
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "NEWHOPE"


def test_python_str_enums_can_be_passed_directly_to_make_executable_schema():
    class Episode(str, Enum):
        NEWHOPE = "new-hope"
        EMPIRE = "empire-strikes"
        JEDI = "return-jedi"

    query = QueryType()
    query.set_field("testEnum", lambda *_: Episode.NEWHOPE)

    schema = make_executable_schema([enum_definition, enum_field], query, Episode)
    result = graphql_sync(schema, "{ testEnum }")
    assert result.data["testEnum"] == "NEWHOPE"


def test_error_is_raised_for_python_enum_with_name_not_in_schema():
    class UnknownEnum(str, Enum):
        NEWHOPE = "new-hope"
        EMPIRE = "empire-strikes"
        JEDI = "return-jedi"

    query = QueryType()
    query.set_field("testEnum", lambda *_: UnknownEnum.NEWHOPE)

    with pytest.raises(ValueError):
        make_executable_schema([enum_definition, enum_field], query, UnknownEnum)
