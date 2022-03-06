import pytest
from graphql import GraphQLError, graphql_sync

from ariadne import SchemaDirectiveVisitor

from ..deferred_type import DeferredType
from ..directive_type import DirectiveType
from ..enum_type import EnumType
from ..executable_schema import make_executable_schema
from ..input_type import InputType
from ..interface_type import InterfaceType
from ..object_type import ObjectType
from ..scalar_type import ScalarType


def test_input_type_raises_attribute_error_when_defined_without_schema(snapshot):
    with pytest.raises(AttributeError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            pass

    snapshot.assert_match(err)


def test_input_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = True

    snapshot.assert_match(err)


def test_input_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = "inpet UserInput"

    snapshot.assert_match(err)


def test_input_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = """
            type User {
                id: ID!
            }
            """

    snapshot.assert_match(err)


def test_input_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = """
            input User

            input Group
            """

    snapshot.assert_match(err)


def test_input_type_raises_error_when_defined_without_fields(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = "input User"

    snapshot.assert_match(err)


def test_input_type_extracts_graphql_name():
    class UserInput(InputType):
        __schema__ = """
        input User {
            id: ID!
        }
        """

    assert UserInput.graphql_name == "User"


def test_input_type_raises_error_when_defined_without_field_type_dependency(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = """
            input User {
                id: ID!
                role: Role!
            }
            """

    snapshot.assert_match(err)


def test_input_type_verifies_field_dependency():
    # pylint: disable=unused-variable
    class RoleEnum(EnumType):
        __schema__ = """
        enum Role {
            USER
            ADMIN
        }
        """

    class UserInput(InputType):
        __schema__ = """
        input User {
            id: ID!
            role: Role!
        }
        """
        __requires__ = [RoleEnum]


def test_input_type_verifies_circular_dependency():
    # pylint: disable=unused-variable
    class UserInput(InputType):
        __schema__ = """
        input User {
            id: ID!
            patron: User
        }
        """


def test_input_type_verifies_circular_dependency_using_deferred_type():
    # pylint: disable=unused-variable
    class GroupInput(InputType):
        __schema__ = """
        input Group {
            id: ID!
            patron: User
        }
        """
        __requires__ = [DeferredType("User")]

    class UserInput(InputType):
        __schema__ = """
        input User {
            id: ID!
            group: Group
        }
        """
        __requires__ = [GroupInput]


def test_input_type_can_be_extended_with_new_fields():
    # pylint: disable=unused-variable
    class UserInput(InputType):
        __schema__ = """
        input User {
            id: ID!
        }
        """

    class ExtendUserInput(InputType):
        __schema__ = """
        extend input User {
            name: String!
        }
        """
        __requires__ = [UserInput]


def test_input_type_can_be_extended_with_directive():
    # pylint: disable=unused-variable
    class ExampleDirective(DirectiveType):
        __schema__ = "directive @example on INPUT_OBJECT"
        __visitor__ = SchemaDirectiveVisitor

    class UserInput(InputType):
        __schema__ = """
        input User {
            id: ID!
        }
        """

    class ExtendUserInput(InputType):
        __schema__ = """
        extend input User @example
        """
        __requires__ = [UserInput, ExampleDirective]


def test_input_type_raises_error_when_defined_without_extended_dependency(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExtendUserInput(InputType):
            __schema__ = """
            extend input User {
                name: String!
            }
            """

    snapshot.assert_match(err)


def test_input_type_raises_error_when_extended_dependency_is_wrong_type(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleInterface(InterfaceType):
            __schema__ = """
            interface User {
                id: ID!
            }
            """

        class ExtendUserInput(InputType):
            __schema__ = """
            extend input User {
                name: String!
            }
            """
            __requires__ = [ExampleInterface]

    snapshot.assert_match(err)


def test_input_type_raises_error_when_defined_with_args_map_for_nonexisting_field(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserInput(InputType):
            __schema__ = """
            input User {
                id: ID!
            }
            """
            __args__ = {
                "fullName": "full_name",
            }

    snapshot.assert_match(err)


class UserInput(InputType):
    __schema__ = """
    input UserInput {
        id: ID!
        fullName: String!
    }
    """
    __args__ = {
        "fullName": "full_name",
    }


class GenericScalar(ScalarType):
    __schema__ = "scalar Generic"


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        reprInput(input: UserInput): Generic!
    }
    """
    __aliases__ = {"reprInput": "repr_input"}
    __requires__ = [GenericScalar, UserInput]

    def resolve_repr_input(*_, input):  # pylint: disable=redefined-builtin
        return input


schema = make_executable_schema(QueryType)


def test_input_type_maps_args_to_python_dict_keys():
    result = graphql_sync(schema, '{ reprInput(input: {id: "1", fullName: "Alice"}) }')
    assert result.data == {
        "reprInput": {"id": "1", "full_name": "Alice"},
    }
