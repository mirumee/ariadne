from dataclasses import dataclass

import pytest
from graphql import GraphQLError

from ..object_type import ObjectType
from ..union_type import UnionType


def test_union_type_raises_error_when_defined_without_schema(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class ExampleUnion(UnionType):
            pass

    snapshot.assert_match(err)


def test_union_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class ExampleUnion(UnionType):
            __schema__ = True

    snapshot.assert_match(err)


def test_union_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class ExampleUnion(UnionType):
            __schema__ = "unien Example = A | B"

    snapshot.assert_match(err)


def test_union_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleUnion(UnionType):
            __schema__ = "scalar DateTime"

    snapshot.assert_match(err)


def test_union_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleUnion(UnionType):
            __schema__ = """
            union A = C | D

            union B = C | D
            """

    snapshot.assert_match(err)


@dataclass
class User:
    id: int
    name: str


@dataclass
class Comment:
    id: int
    message: str


class UserType(ObjectType):
    __schema__ = """
    type User {
        id: ID!
        name: String!
    }
    """


class CommentType(ObjectType):
    __schema__ = """
    type Comment {
        id: ID!
        message: String!
    }
    """


def test_union_type_extracts_graphql_name():
    class ExampleUnion(UnionType):
        __schema__ = "union Example = User | Comment"
        __requires__ = [UserType, CommentType]

    assert ExampleUnion.graphql_name == "Example"


def test_union_type_raises_error_when_defined_without_member_type_dependency(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleUnion(UnionType):
            __schema__ = "union Example = User | Comment"
            __requires__ = [UserType]

    snapshot.assert_match(err)
