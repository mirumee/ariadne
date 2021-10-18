import re
from enum import Enum, IntEnum

import pytest
from graphql import graphql_sync, build_schema, parse
from graphql.pyutils.undefined import Undefined
from graphql.utilities.build_ast_schema import build_ast_schema

from ariadne import EnumType, QueryType, make_executable_schema
from ariadne import graphql_sync as ariadne_graphql_sync
from ariadne.executable_schema import join_type_defs
from ariadne.enums import find_enum_values_in_schema

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


def test_input_exc_schema_raises_exception_for_undefined_enum_value_in_flat_input():
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
            "Value for type: <Episode> is invalid. "
            "Check InputField/Arguments for <role> in <Test> (Undefined enum value)."
        ),
    ):
        make_executable_schema([enum_definition, input_schema])


def test_input_exc_schema_raises_exception_for_undefined_enum_value_in_nested_object():
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
            "Value for type: <Test> is invalid. "
            "Check InputField/Arguments for <test> in <BetterTest> (Undefined enum value)."
        ),
    ):
        make_executable_schema([enum_definition, input_schema])


def test_input_exc_schema_raises_exception_for_undefined_enum_value_in_nested_field_arg():
    input_schema = """
        type Query {
            complex(i: BetterTest = { test: { role: TWO_TOWERS } }): String
        }
        input Test {
            ignore: String 
            role: Episode = EMPIRE  
        }
        input BetterTest {
            newIgnore: String
            test: Test = { role: NEW_HOPE }
        }
    """

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Value for type: <BetterTest> is invalid. "
            "Check InputField/Arguments for <i> in <Query> (Undefined enum value)."
        ),
    ):
        make_executable_schema([enum_definition, input_schema])


def test_find_enum_values_in_schema_for_undefined_and_invalid_values():
    input_schema = """
        type Query {
            complex(hello: Episode = EMPIRE,
                    hi: Test = { role: JEDI,  next_role: ENTERPRISE, ignore: "HI"}, 
                    bonjour: BetterTest = {newIgnore: "Witam", test: { role: NEWHOPE }}): String
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
    query_complex_keys = [["next_role"], ["role"], ["test", "role"]]
    better_test_complex_keys = [["role"]]
    number_of_defined_enum_values = 7

    # 2 Undefined because of "ENTERPRISE" invalid value, and next_role in Test input
    number_of_undefined_default_enum_values = 3

    ast_document = parse(join_type_defs([enum_definition, input_schema]))
    schema = build_ast_schema(ast_document)
    enums_entities = list(find_enum_values_in_schema(schema))
    keys_to_complex_inputs = [keys for *_, keys in enums_entities if keys is not None]

    undefined = [
        (*_, args, keys)
        for *_, args, keys in enums_entities
        if args.default_value is Undefined
    ]

    assert keys_to_complex_inputs == query_complex_keys + better_test_complex_keys
    assert len(enums_entities) == number_of_defined_enum_values
    assert len(undefined) == number_of_undefined_default_enum_values


def test_enum_type_is_able_to_represent_enum_default_value_in_schema():
    #  regression test for: https://github.com/mirumee/ariadne/issues/293

    type_defs = """
        enum Role {
            ADMIN
            USER
        }

        type Query {
            hello(r: Role = USER): String
        }
    """

    class Role(Enum):
        ADMIN = "admin"
        USER = "user"

    def resolve_test_enum(*_, r):
        return r == Role.USER

    RoleGraphQLType = EnumType("Role", Role)
    QueryGraphQLType = QueryType()

    QueryGraphQLType.set_field("hello", resolve_test_enum)

    schema = make_executable_schema(
        type_defs,
        QueryGraphQLType,
        RoleGraphQLType,
    )

    query = "{__schema{types{name,fields{name,args{name,defaultValue}}}}}"
    _, result = ariadne_graphql_sync(schema, {"query": query}, debug=True)
    types_map = {
        result_type["name"]: result_type
        for result_type in result["data"]["__schema"]["types"]
    }
    assert schema.type_map["Query"].fields["hello"].args["r"].default_value == Role.USER

    result_hello_query = graphql_sync(schema, "{hello}")
    assert types_map["Query"]["fields"][0]["args"][0]["defaultValue"] == "USER"
    assert result_hello_query.data["hello"]
    assert result_hello_query.errors is None
