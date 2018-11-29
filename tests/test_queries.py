from unittest.mock import Mock

from graphql import graphql_sync

from ariadne import ResolverMap, make_executable_schema, resolve_to


def test_query_root_type_default_resolver():
    type_defs = """
        type Query {
            test: String
        }
    """

    query = ResolverMap("Query")
    query.field("test")(lambda *_: "success")

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test }")
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

    query = ResolverMap("Query")
    query.field("test")(lambda *_: {"node": "custom"})

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test { node } }")
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

    query = ResolverMap("Query")
    query.field("test")(lambda *_: Mock(node="custom"))

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test { node } }")
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

    query = ResolverMap("Query")
    query.field("test")(lambda *_: {"node": "custom"})

    custom = ResolverMap("Custom")
    custom.field("node")(lambda *_: "deep")

    schema = make_executable_schema(type_defs, [query, custom])

    result = graphql_sync(schema, "{ test { node } }")
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

    query = ResolverMap("Query")
    query.field("test")(lambda *_: {"node": "custom", "default": "ok"})

    custom = ResolverMap("Custom")
    custom.field("node")(lambda *_: "deep")

    schema = make_executable_schema(type_defs, [query, custom])

    result = graphql_sync(schema, "{ test { node default } }")
    assert result.errors is None
    assert result.data == {"test": {"node": "deep", "default": "ok"}}


def test_query_with_argument():
    type_defs = """
        type Query {
            test(returnValue: Int!): Int
        }
    """

    query = ResolverMap("Query")

    @query.field("test")
    def resolve_test(*_, returnValue):
        assert returnValue == 4
        return "42"

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test(returnValue: 4) }")
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

    query = ResolverMap("Query")

    @query.field("test")
    def resolve_test(*_, data):
        assert data == {"value": 4}
        return "42"

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test(data: { value: 4 }) }")
    assert result.errors is None
    assert result.data == {"test": 42}


def test_alias_resolver():
    type_defs = """
        type Query {
            user: User
        }

        type User {
            firstName: String
        }
    """

    query = ResolverMap("Query")
    query.field("user")(lambda *_: {"first_name": "Joe"})

    user = ResolverMap("User")
    user.alias("firstName", "first_name")

    schema = make_executable_schema(type_defs, [query, user])

    result = graphql_sync(schema, "{ user { firstName } }")
    assert result.errors is None
    assert result.data == {"user": {"firstName": "Joe"}}


def test_alias_resolver_to_object_attribute():
    type_defs = """
        type Query {
            user: User
        }

        type User {
            firstName: String
        }
    """

    query = ResolverMap("Query")
    query.field("user")(lambda *_: Mock(first_name="Joe"))

    user = ResolverMap("User")
    user.alias("firstName", "first_name")

    schema = make_executable_schema(type_defs, [query, user])

    result = graphql_sync(schema, "{ user { firstName } }")
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

    query = ResolverMap("Query")
    query.field("user")(lambda *_: mock_user)

    user = ResolverMap("User")
    user.alias("firstName", "first_name")
    user.alias("blogPosts", "blog_posts")

    schema = make_executable_schema(type_defs, [query, user])

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

    result = graphql_sync(schema, query, variable_values=variables)
    assert result.errors is None
    assert result.data == {
        "user": {"firstName": first_name, "avatar": avatar, "blogPosts": blog_posts}
    }
    mock_user.avatar.assert_called_with(size=variables["size"])
    mock_user.blog_posts.assert_called_once_with(published=variables["published"])
