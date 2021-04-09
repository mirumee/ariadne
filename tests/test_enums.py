import re
from enum import Enum, IntEnum

import pytest
from graphql import graphql_sync, build_schema

from ariadne import EnumType, QueryType, make_executable_schema
from ariadne.executable_schema import find_enum_values_in_schema

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
    result = graphql_sync(schema, "{ testEnum(value: %s) }" % "NEWHOPE")
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
    result = graphql_sync(schema, "{ testEnum(value: %s) }" % "INVALID")
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
        graphql_enum.bind_to_schema(schema_with_enum)  # pylint: disable=no-member


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
    result = graphql_sync(schema, "{ testEnum(value: %s) }" % "NEWHOPE")
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


@pytest.mark.skip(reason="TBD")
def test_flat_query_with_default_enum():
    enum_param_default = """
       type Query {
           testEnum(value: Episode! = EMPIRE): Boolean!
       }
    """
    query = QueryType()

    def resolv(*_, value):
        return value == PyIntEnum.EMPIRE

    query.set_field("testEnum", resolv)
    schema = make_executable_schema(
        [enum_definition, enum_param_default], [query, int_enum]
    )
    result = graphql_sync(schema, "{ testEnum }")

    assert result.data["testEnum"]
    assert result.errors is None


@pytest.mark.skip(reason="TBD")
def test_input_with_default_enum():
    input_param_default = """
        type Query {
            testEnum(input: QueryInput): Boolean!
        }
         input QueryInput {
            value: Episode! = EMPIRE
        }
    """
    query = QueryType()

    def resolv(_, __, input_):
        return input_["value"] == PyIntEnum.EMPIRE

    query.set_field("testEnum", resolv)
    schema = make_executable_schema(
        [enum_definition, input_param_default], [query, int_enum]
    )
    result = graphql_sync(schema, "{ testEnum(input: QueryInput) }")

    assert result.errors is None
    assert result.data["testEnum"]


def test_input_exc_schema_should_raise_an_exception_if_undefined_enum_flat_input():
    input_schema = """
         type Query {
            complex(i: Test = { role: EMPIRE }): String
        }
        input Test {
            ignore: String
            role: Episode = TWO_TOWERS  
        }
    """
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Value for type: <Test> at field: <role> is invalid (undefined enum value)."
        ),
    ):
        make_executable_schema([enum_definition, input_schema])


def test_input_exc_schema_should_raise_an_exception_if_undefined_enum_in_nested_input():
    input_schema = """
        type Query {
            complex(i: Test = { role: EMPIRE }): String
        }
        input Test {
            ignore: String 
            role: Episode = EMPIRE  
        }
        input BetterTest {
            newIgnore: String
            test: Test = { role: ANDRZEJU }
        }
    """

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Value for type: <BetterTest> at field: <test> is invalid (undefined enum value)."
        ),
    ):
        make_executable_schema([enum_definition, input_schema])


def test_find_args_and_inputs_from_schema():
    input_schema = """
        type Query {
            complex(i: Test = { role: JEDI }): String
        }
        input Test {
            ignore: String 
            role: Episode = EMPIRE  
            next_role: Episode
        }
        input BetterTest {
            newIgnore: String
            test: Test = { role: NEWHOPE }
        }
    """

    schema = make_executable_schema([enum_definition, input_schema])
    # print(schema.type_map["Query"].fields["complex"].args["i"].ast_node.default_value.fields[0].name.value)
    g = find_enum_values_in_schema(schema)
    result, keys = next(g)
    assert keys == ["role"]
    assert result.default_value[keys[0]] == "JEDI"
