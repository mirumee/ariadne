import pytest
from graphql import GraphQLError, graphql_sync

from ..executable_schema import make_executable_schema
from ..mutation_type import MutationType
from ..object_type import ObjectType


def test_mutation_type_raises_attribute_error_when_defined_without_schema(snapshot):
    with pytest.raises(AttributeError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            pass

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = True

    snapshot.assert_match(err)


def test_object_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = "typo User"

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = "scalar DateTime"

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type User

            type Group
            """

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_for_different_type_name(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type User {
                id: ID!
            }
            """

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_without_fields(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type Mutation
            """

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_with_multiple_fields(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type Mutation {
                userCreate(name: String!): Boolean!
                userUpdate(id: ID!, name: String!): Boolean!
            }
            """

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_without_resolve_mutation_attr(
    snapshot,
):
    with pytest.raises(AttributeError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type Mutation {
                userCreate(name: String!): Boolean!
            }
            """

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_without_callable_resolve_mutation_attr(
    snapshot,
):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type Mutation {
                userCreate(name: String!): Boolean!
            }
            """

            resolve_mutation = True

    snapshot.assert_match(err)


def test_mutation_type_raises_error_when_defined_without_return_type_dependency(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UserCreateMutation(MutationType):
            __schema__ = """
            type Mutation {
                userCreate(name: String!): UserCreateResult!
            }
            """

            @staticmethod
            def resolve_mutation(*_args):
                pass

    snapshot.assert_match(err)


def test_mutation_type_verifies_field_dependency():
    # pylint: disable=unused-variable
    class UserCreateResult(ObjectType):
        __schema__ = """
        type UserCreateResult {
            errors: [String!]
        }
        """

    class UserCreateMutation(MutationType):
        __schema__ = """
        type Mutation {
            userCreate(name: String!): UserCreateResult!
        }
        """
        __requires__ = [UserCreateResult]

        @staticmethod
        def resolve_mutation(*_args):
            pass


class QueryType(ObjectType):
    __schema__ = """
    type Query {
        field: String!
    }
    """


class ResultType(ObjectType):
    __schema__ = """
    type Result {
        error: String
        total: Int
    }
    """


class SumMutation(MutationType):
    __schema__ = """
    type Mutation {
        sum(a: Int!, b: Int!): Result!
    }
    """
    __requires__ = [ResultType]

    @staticmethod
    def resolve_mutation(*_, a: int, b: int):
        return {"total": a + b}


class DivideMutation(MutationType):
    __schema__ = """
    type Mutation {
        divide(a: Int!, b: Int!): Result!
    }
    """
    __requires__ = [ResultType]

    @staticmethod
    def resolve_mutation(*_, a: int, b: int):
        if a == 0 or b == 0:
            return {"error": "Division by zero"}

        return {"total": a / b}


schema = make_executable_schema(QueryType, SumMutation, DivideMutation)


def test_sum_mutation_resolves_to_result():
    query = """
    mutation {
        sum(a: 5, b: 3) {
            total
            error
        }
    }
    """
    result = graphql_sync(schema, query)
    assert result.data == {
        "sum": {
            "total": 8,
            "error": None,
        },
    }


def test_divide_mutation_resolves_to_result():
    query = """
    mutation {
        divide(a: 6, b: 3) {
            total
            error
        }
    }
    """
    result = graphql_sync(schema, query)
    assert result.data == {
        "divide": {
            "total": 2,
            "error": None,
        },
    }


def test_divide_mutation_resolves_to_error_result():
    query = """
    mutation {
        divide(a: 6, b: 0) {
            total
            error
        }
    }
    """
    result = graphql_sync(schema, query)
    assert result.data == {
        "divide": {
            "total": None,
            "error": "Division by zero",
        },
    }
