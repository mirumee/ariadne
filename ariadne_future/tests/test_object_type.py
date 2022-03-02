import pytest
from graphql import GraphQLError, graphql_sync

from ariadne import SchemaDirectiveVisitor

from ..deferred_type import DeferredType
from ..directive_type import DirectiveType
from ..executable_schema import make_executable_schema
from ..interface_type import InterfaceType
from ..object_type import ObjectType


def test_object_type_raises_error_when_defined_without_schema(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            pass

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = True

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = "typo User"

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = "scalar DateTime"

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = """
            type User

            type Group
            """

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_without_fields(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = "type User"

    snapshot.assert_match(err)


def test_object_type_extracts_graphql_name():
    class GroupType(ObjectType):
        __schema__ = """
        type Group {
            id: ID!
        }
        """

    assert GroupType.graphql_name == "Group"


def test_object_type_raises_error_when_defined_without_return_type_dependency(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = """
            type User {
                group: Group
                groups: [Group!]
            }
            """

    snapshot.assert_match(err)


def test_object_type_verifies_field_dependency():
    # pylint: disable=unused-variable
    class GroupType(ObjectType):
        __schema__ = """
        type Group {
            id: ID!
        }
        """

    class UserType(ObjectType):
        __schema__ = """
        type User {
            group: Group
            groups: [Group!]
        }
        """
        __requires__ = [GroupType]


def test_object_type_verifies_circular_dependency():
    # pylint: disable=unused-variable
    class UserType(ObjectType):
        __schema__ = """
        type User {
            follows: User
        }
        """


def test_object_type_raises_error_when_defined_without_argument_type_dependency(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = """
            type User {
                actions(input: UserInput): [String!]!
            }
            """

    snapshot.assert_match(err)


def test_object_type_verifies_circular_dependency_using_deferred_type():
    # pylint: disable=unused-variable
    class GroupType(ObjectType):
        __schema__ = """
        type Group {
            id: ID!
            users: [User]
        }
        """
        __requires__ = [DeferredType("User")]

    class UserType(ObjectType):
        __schema__ = """
        type User {
            group: Group
        }
        """
        __requires__ = [GroupType]


def test_object_type_can_be_extended_with_new_fields():
    # pylint: disable=unused-variable
    class UserType(ObjectType):
        __schema__ = """
        type User {
            id: ID!
        }
        """

    class ExtendUserType(ObjectType):
        __schema__ = """
        extend type User {
            name: String
        }
        """
        __requires__ = [UserType]


def test_object_type_can_be_extended_with_directive():
    # pylint: disable=unused-variable
    class ExampleDirective(DirectiveType):
        __schema__ = "directive @example on OBJECT"
        __visitor__ = SchemaDirectiveVisitor

    class UserType(ObjectType):
        __schema__ = """
        type User {
            id: ID!
        }
        """

    class ExtendUserType(ObjectType):
        __schema__ = """
        extend type User @example
        """
        __requires__ = [UserType, ExampleDirective]


def test_object_type_can_be_extended_with_interface():
    # pylint: disable=unused-variable
    class ExampleInterface(InterfaceType):
        __schema__ = """
        interface Interface {
            id: ID!
        }
        """

    class UserType(ObjectType):
        __schema__ = """
        type User {
            id: ID!
        }
        """

    class ExtendUserType(ObjectType):
        __schema__ = """
        extend type User implements Interface
        """
        __requires__ = [UserType, ExampleInterface]


def test_object_type_raises_error_when_defined_without_extended_dependency(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExtendUserType(ObjectType):
            __schema__ = """
            extend type User {
                name: String
            }
            """

    snapshot.assert_match(err)


def test_object_type_raises_error_when_extended_dependency_is_wrong_type(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleInterface(InterfaceType):
            __schema__ = """
            interface Example {
                id: ID!
            }
            """

        class ExampleType(ObjectType):
            __schema__ = """
            extend type Example {
                name: String
            }
            """
            __requires__ = [ExampleInterface]

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_alias_for_nonexisting_field(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = """
            type User {
                name: String
            }
            """
            __aliases__ = {
                "joinedDate": "joined_date",
            }

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_resolver_for_nonexisting_field(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserType(ObjectType):
            __schema__ = """
            type User {
                name: String
            }
            """

            @staticmethod
            def resolve_group(*_):
                return None

    snapshot.assert_match(err)


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        field: String!
        other: String!
        firstField: String!
        secondField: String!
    }
    """
    __aliases__ = {
        "firstField": "first_field",
        "secondField": "second_field",
    }

    @staticmethod
    def resolve_other(*_):
        return "Word Up!"

    @staticmethod
    def resolve_second_field(obj, *_):
        return "Obj: %s" % obj["secondField"]


schema = make_executable_schema(QueryType)


def test_object_resolves_field_with_default_resolver():
    result = graphql_sync(schema, "{ field }", root_value={"field": "Hello!"})
    assert result.data["field"] == "Hello!"


def test_object_resolves_field_with_custom_resolver():
    result = graphql_sync(schema, "{ other }")
    assert result.data["other"] == "Word Up!"


def test_object_resolves_field_with_aliased_default_resolver():
    result = graphql_sync(
        schema, "{ firstField }", root_value={"first_field": "Howdy?"}
    )
    assert result.data["firstField"] == "Howdy?"


def test_object_resolves_field_with_aliased_custom_resolver():
    result = graphql_sync(schema, "{ secondField }", root_value={"secondField": "Hey!"})
    assert result.data["secondField"] == "Obj: Hey!"
