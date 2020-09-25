from attr import dataclass

import pytest
from graphql import graphql_sync

from ariadne import (
    QueryType,
    UnionType,
    make_executable_schema,
)

type_defs = """
    union Result = Book | Author

    type Book {
        title: String
    }

    type Author {
        name: String
    }

    type Query {
        item: Result
    }
"""


test_query = """
    {
        item {
            __typename
            ... on Book {
                title
            }
            ... on Author {
                name
            }
        }
    }
"""


@dataclass
class Book:
    title: str = "Shantaram"


@dataclass
class Author:
    name: str = "Gregory David Roberts"


@pytest.fixture
def query():
    return QueryType()


@pytest.fixture
def query_with_book_item(query):
    query.set_field("item", lambda *_: Book())
    return query


@pytest.fixture
def query_with_author_item(query):
    query.set_field("item", lambda *_: Author())
    return query


@pytest.fixture
def query_with_none_item(query):
    query.set_field("item", lambda *_: 42)
    return query


@pytest.fixture
def union_type():
    union = UnionType("Result")
    return union


def test_default_type_resolver_foo(query_with_book_item, union_type):
    schema = make_executable_schema(type_defs, [query_with_book_item, union_type])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": {"__typename": "Book", "title": "Shantaram"}}


def test_default_type_resolver_bar(query_with_author_item, union_type):
    schema = make_executable_schema(type_defs, [query_with_author_item, union_type])
    result = graphql_sync(schema, test_query)
    assert result.data == {
        "item": {"__typename": "Author", "name": "Gregory David Roberts"}
    }


def test_default_type_resolver_None(query_with_none_item, union_type):
    schema = make_executable_schema(type_defs, [query_with_none_item, union_type])
    result = graphql_sync(schema, test_query)
    assert result.data == {"item": None}
