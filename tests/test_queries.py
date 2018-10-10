from unittest.mock import Mock

from graphql import graphql

from ariadne import make_executable_schema, resolve_to


def test_query_root_type_default_resolver():
    type_defs = """
        type Query {
            test: String
        }
    """

    resolvers = {"Query": {"test": lambda *_: "success"}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test }")
    assert result.errors is None
    assert result.data == {"test": "success"}


def test_query_custom_type_default_resolver():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
        }
    """

    resolvers = {"Query": {"test": lambda *_: {"node": "custom"}}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test { node } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "custom"}}


def test_query_custom_type_object_default_resolver():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
        }
    """

    resolvers = {"Query": {"test": lambda *_: Mock(node="custom")}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test { node } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "custom"}}


def test_query_custom_type_custom_resolver():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
        }
    """

    resolvers = {
        "Query": {"test": lambda *_: {"node": "custom"}},
        "Custom": {"node": lambda *_: "deep"},
    }

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test { node } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "deep"}}


def test_query_custom_type_merged_custom_default_resolvers():
    type_defs = """
        type Query {
            test: Custom
        }

        type Custom {
            node: String
            default: String
        }
    """

    resolvers = {
        "Query": {"test": lambda *_: {"node": "custom", "default": "ok"}},
        "Custom": {"node": lambda *_: "deep"},
    }

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test { node default } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "deep", "default": "ok"}}


def test_query_with_argument():
    type_defs = """
        type Query {
            test(returnValue: Int!): Int
        }
    """

    def resolve_test(*_, returnValue):
        assert returnValue == 4
        return "42"

    resolvers = {"Query": {"test": resolve_test}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test(returnValue: 4) }")
    assert result.errors is None
    assert result.data == {"test": 42}


def test_query_with_input():
    type_defs = """
        type Query {
            test(data: TestInput): Int
        }

        input TestInput {
            value: Int
        }
    """

    def resolve_test(*_, data):
        assert data == {"value": 4}
        return "42"

    resolvers = {"Query": {"test": resolve_test}}

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ test(data: { value: 4 }) }")
    assert result.errors is None
    assert result.data == {"test": 42}


def test_mapping_resolver():
    type_defs = """
        type Query {
            user: User
        }

        type User {
            firstName: String
        }
    """

    resolvers = {
        "Query": {"user": lambda *_: {"first_name": "Joe"}},
        "User": {"firstName": resolve_to("first_name")},
    }

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ user { firstName } }")
    assert result.errors is None
    assert result.data == {"user": {"firstName": "Joe"}}


def test_mapping_resolver_to_object_attribute():
    type_defs = """
        type Query {
            user: User
        }

        type User {
            firstName: String
        }
    """

    resolvers = {
        "Query": {"user": lambda *_: Mock(first_name="Joe")},
        "User": {"firstName": resolve_to("first_name")},
    }

    schema = make_executable_schema(type_defs, resolvers)

    result = graphql(schema, "{ user { firstName } }")
    assert result.errors is None
    assert result.data == {"user": {"firstName": "Joe"}}


def test_default_resolver(mock_user, first_name, avatar, blog_posts):
    type_defs = """
        type Query {
            user: User
        }

        type User {
            firstName: String
            avatar(size: String): String
            blogPosts(published: Boolean): Int
        }
    """

    resolvers = {
        "Query": {"user": lambda *_: mock_user},
        "User": {
            "firstName": resolve_to("first_name"),
            "blogPosts": resolve_to("blog_posts"),
        },
    }

    schema = make_executable_schema(type_defs, resolvers)

    query = """
     query User($size: String, $published: Boolean) {
      user {
        firstName
        avatar(size: $size)
        blogPosts(published: $published)
      }
    }
    """
    variables = {"size": "200x300", "published": True}

    result = graphql(schema, query, variables=variables)
    assert result.errors is None
    assert result.data == {
        "user": {"firstName": first_name, "avatar": avatar, "blogPosts": blog_posts}
    }
    mock_user.avatar.assert_called_with(size=variables["size"])
    mock_user.blog_posts.assert_called_once_with(published=variables["published"])
