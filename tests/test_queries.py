from unittest.mock import Mock

from graphql import graphql_sync

from ariadne import ResolverMap, make_executable_schema


def test_default_resolver_resolves_value_from_dict_item():
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


def test_default_resolver_resolves_value_from_object_attr():
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


def test_custom_resolver_is_called_to_resolve_custom_type_field_value():
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


def test_custom_and_default_resolvers_are_combined_to_resolve_custom_type_fields():
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


def test_custom_resolver_is_called_with_arguments_passed_with_query():
    type_defs = """
        type Query {
            test(returnValue: Int!): Int
        }
    """

    query = ResolverMap("Query")

    @query.field("test")
    def resolve_test(*_, returnValue):  # pylint: disable=unused-variable
        assert returnValue == 4
        return "42"

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test(returnValue: 4) }")
    assert result.errors is None
    assert result.data == {"test": 42}


def test_custom_resolver_is_called_with_input_type_value_as_dict():
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
    def resolve_test(*_, data):  # pylint: disable=unused-variable
        assert data == {"value": 4}
        return "42"

    schema = make_executable_schema(type_defs, query)

    result = graphql_sync(schema, "{ test(data: { value: 4 }) }")
    assert result.errors is None
    assert result.data == {"test": 42}


def test_default_resolver_calls_resolved_attr_with_arguments_if_its_callable(
    mock_user, first_name, avatar, blog_posts
):
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
