import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from graphql import (
    GraphQLField,
    GraphQLInt,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
)
from sqlalchemy.orm import joinedload, selectinload

from ariadne import make_executable_schema
from ariadne.contrib.sqlalchemy import (
    SQLAlchemyObjectType,
    SQLAlchemyQueryType,
)

TYPE_DEFS = """
    type Query {
        users: [User!]!
        user(id: ID!): User
        posts: [Post!]!
        tags: [Tag!]!
        ping: String
    }

    type User {
        id: ID!
        username: String!
        posts: [Post!]!
    }

    type Post {
        id: ID!
        title: String!
        author: User!
        tags: [Tag!]!
    }

    type Tag {
        id: ID!
        name: String!
        posts: [Post!]!
    }
"""


def _make_object_types(models):
    return (
        SQLAlchemyObjectType("User", models["User"]),
        SQLAlchemyObjectType("Post", models["Post"]),
        SQLAlchemyObjectType("Tag", models["Tag"]),
    )


def _make_sync_session(scalar_first=None, scalar_all=None):
    """Build a sync session whose `.execute(stmt)` chain returns the configured
    scalars.first() and scalars().unique().all() values."""
    scalars = Mock()
    scalars.first.return_value = scalar_first
    unique = Mock()
    unique.all.return_value = scalar_all if scalar_all is not None else []
    scalars.unique.return_value = unique

    result = Mock()
    result.scalars.return_value = scalars

    session = Mock()
    session.execute.return_value = result
    return session


def _make_async_session(scalar_first=None, scalar_all=None):
    """Async-style session whose `.execute(...)` returns an awaitable result."""
    scalars = Mock()
    scalars.first.return_value = scalar_first
    unique = Mock()
    unique.all.return_value = scalar_all if scalar_all is not None else []
    scalars.unique.return_value = unique

    result = Mock()
    result.scalars.return_value = scalars

    session = Mock()
    session.execute = AsyncMock(return_value=result)
    return session


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestInit:
    def test_inherits_query_name(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        assert query.name == "Query"

    def test_indexes_object_types_by_graphql_name(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        assert query.object_types == {
            "User": user_type,
            "Post": post_type,
            "Tag": tag_type,
        }

    def test_indexes_object_types_by_model_class(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        assert query._object_types_by_model == {
            models["User"]: user_type,
            models["Post"]: post_type,
            models["Tag"]: tag_type,
        }

    def test_accepts_empty_sequence(self):
        query = SQLAlchemyQueryType([])

        assert query.object_types == {}
        assert query._object_types_by_model == {}


# ---------------------------------------------------------------------------
# get_session_from_context
# ---------------------------------------------------------------------------


class TestGetSessionFromContext:
    def test_returns_value_from_default_key(self):
        session = Mock(name="session")

        assert (
            SQLAlchemyQueryType.get_session_from_context({"session": session})
            is session
        )

    def test_missing_key_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="session"):
            SQLAlchemyQueryType.get_session_from_context({})

    def test_subclass_can_override_lookup(self):
        class MyQueryType(SQLAlchemyQueryType):
            @staticmethod
            def get_session_from_context(context):
                return context["request"].state.session

        session = Mock(name="session")
        context = {"request": SimpleNamespace(state=SimpleNamespace(session=session))}

        assert MyQueryType.get_session_from_context(context) is session


# ---------------------------------------------------------------------------
# bind_to_schema
# ---------------------------------------------------------------------------


class TestBindToSchema:
    def test_binds_auto_resolvers_to_known_types(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        schema = make_executable_schema(
            TYPE_DEFS, [query, user_type, post_type, tag_type]
        )

        query_obj = schema.type_map["Query"]
        # Every field whose type is one of our SQLAlchemyObjectTypes must have
        # an auto-resolver wired up.
        assert query_obj.fields["users"].resolve is not None
        assert query_obj.fields["posts"].resolve is not None
        assert query_obj.fields["tags"].resolve is not None
        assert query_obj.fields["user"].resolve is not None

        # The resolvers also live in the bindable's `_resolvers` map.
        assert "users" in query._resolvers
        assert "posts" in query._resolvers
        assert "tags" in query._resolvers
        assert "user" in query._resolvers

    def test_does_not_bind_auto_resolver_for_unknown_type(self, models):
        # `ping: String` returns a scalar with no matching SQLAlchemyObjectType.
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        make_executable_schema(TYPE_DEFS, [query, user_type, post_type, tag_type])

        assert "ping" not in query._resolvers

    def test_does_not_overwrite_existing_resolver(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        @query.field("users")
        def custom_users(*_):  # pragma: no cover - identity check only
            return []

        make_executable_schema(TYPE_DEFS, [query, user_type, post_type, tag_type])

        assert query._resolvers["users"] is custom_users

    def test_unwraps_list_and_nonnull_wrappers(self, models):
        """`[User!]!` and `User!` and bare `User` must all resolve to the same
        target name `User`. The list wrapper toggles `return_list`."""
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        make_executable_schema(TYPE_DEFS, [query, user_type, post_type, tag_type])

        # both list and scalar fields had resolvers attached
        assert "users" in query._resolvers  # [User!]!
        assert "user" in query._resolvers  # User (nullable scalar)

    def test_falls_back_to_super_when_query_type_missing(self, models):
        """If the schema has no `Query` GraphQL type, `bind_to_schema` should
        defer to the parent class (which raises ValueError). This is the
        fallback branch that protects from running the auto-binding loop on
        something that isn't a GraphQLObjectType."""
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        # Schema without a "Query" type at all.
        schema = GraphQLSchema(
            types=[
                GraphQLObjectType(
                    "Other", {"x": GraphQLField(GraphQLNonNull(GraphQLInt))}
                )
            ]
        )

        with pytest.raises(ValueError, match="Query"):
            query.bind_to_schema(schema)


# ---------------------------------------------------------------------------
# _create_auto_resolver
# ---------------------------------------------------------------------------


class TestCreateAutoResolver:
    def test_resolver_is_not_a_coroutine_function(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])
        resolver = query._create_auto_resolver(user_type, return_list=True)
        assert not inspect.iscoroutinefunction(resolver)

    def test_calls_get_session_from_context(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        session = _make_sync_session(scalar_all=[])
        info = SimpleNamespace(
            context={"session": session},
            field_nodes=[],
            fragments={},
            schema=None,
        )

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            resolver(None, info)

        session.execute.assert_called_once()

    def test_returns_list_when_return_list_true(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        rows = [Mock(name="user1"), Mock(name="user2")]
        session = _make_sync_session(scalar_all=rows)
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            result = resolver(None, info)

        assert result == rows
        session.execute.return_value.scalars.return_value.unique.assert_called_once()

    def test_returns_first_when_return_list_false(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        sentinel = Mock(name="single_user")
        session = _make_sync_session(scalar_first=sentinel)
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=False)
            result = resolver(None, info)

        assert result is sentinel
        session.execute.return_value.scalars.return_value.first.assert_called_once()

    def test_sync_session_result_is_not_awaitable(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        session = _make_sync_session(scalar_all=[])
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            result = resolver(None, info)

        assert not inspect.isawaitable(result)

    @pytest.mark.asyncio
    async def test_async_session_result_is_awaitable(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        session = _make_async_session(scalar_all=[])
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            result = resolver(None, info)

        assert inspect.isawaitable(result)
        await result  # consume the coroutine to avoid ResourceWarning

    @pytest.mark.asyncio
    async def test_awaits_async_session_execute(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        rows = [Mock(name="user1")]
        session = _make_async_session(scalar_all=rows)
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            result = await resolver(None, info)

        assert result == rows
        session.execute.assert_awaited_once()

    def test_passes_object_type_config_to_auto_eager_load(self, models):
        user_type = SQLAlchemyObjectType("User", models["User"])
        post_type = SQLAlchemyObjectType(
            "Post",
            models["Post"],
            aliases={"my_id": "id"},
            strategies={"author": joinedload, "tags": selectinload},
            max_depth=5,
        )
        query = SQLAlchemyQueryType([user_type, post_type])

        session = _make_sync_session(scalar_all=[])
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ) as eager_mock:
            resolver = query._create_auto_resolver(post_type, return_list=True)
            resolver(None, info)

        # auto_eager_load called with the model + per-type config + the
        # query's model→type registry so nested types can be resolved.
        _stmt, passed_info, passed_model = eager_mock.call_args.args
        kwargs = eager_mock.call_args.kwargs
        assert passed_info is info
        assert passed_model is models["Post"]
        assert kwargs["strategies"] == {"author": joinedload, "tags": selectinload}
        assert kwargs["aliases"] == {"my_id": "id"}
        assert kwargs["max_depth"] == 5
        assert kwargs["type_registry"] == {
            models["User"]: user_type,
            models["Post"]: post_type,
        }

    def test_applies_where_filter_for_known_kwargs(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        session = _make_sync_session(scalar_first=None)
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=False)
            resolver(None, info, id=42)

        # The constructed statement passed to execute should include a WHERE.
        executed_stmt = session.execute.call_args.args[0]
        sql = str(executed_stmt.compile()).lower()
        assert "where" in sql and "users.id" in sql

    def test_resolves_kwarg_through_aliases(self, models):
        # `my_id` GraphQL arg must be translated to `id` column on the model.
        post_type = SQLAlchemyObjectType(
            "Post", models["Post"], aliases={"my_id": "id"}
        )
        query = SQLAlchemyQueryType([post_type])

        session = _make_sync_session(scalar_first=None)
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(post_type, return_list=False)
            resolver(None, info, my_id=7)

        executed_stmt = session.execute.call_args.args[0]
        sql = str(executed_stmt.compile()).lower()
        assert "posts.id" in sql

    def test_unknown_kwargs_are_ignored(self, models):
        user_type, _, _ = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type])

        session = _make_sync_session(scalar_all=[])
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            resolver(None, info, nonexistent_field="ignore-me")

        executed_stmt = session.execute.call_args.args[0]
        sql = str(executed_stmt.compile()).lower()
        assert "where" not in sql

    def test_uses_overridden_session_lookup(self, models):
        class MyQueryType(SQLAlchemyQueryType):
            @staticmethod
            def get_session_from_context(context):
                return context["custom_session"]

        user_type, _, _ = _make_object_types(models)
        query = MyQueryType([user_type])

        session = _make_sync_session(scalar_all=[])
        info = SimpleNamespace(context={"custom_session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(user_type, return_list=True)
            resolver(None, info)

        session.execute.assert_called_once()

    def test_uses_object_types_get_base_query(self, models):
        """Subclasses may override `get_base_query` to apply default filters -
        the auto-resolver must route through it instead of building its own
        `select(model)`."""

        class FilteredPost(SQLAlchemyObjectType):
            def get_base_query(self, info, **kwargs):
                from sqlalchemy import select

                return select(self.model).where(self.model.title == "fixed")

        post_type = FilteredPost("Post", models["Post"])
        query = SQLAlchemyQueryType([post_type])

        session = _make_sync_session(scalar_all=[])
        info = SimpleNamespace(context={"session": session})

        with patch(
            "ariadne.contrib.sqlalchemy.query.auto_eager_load",
            side_effect=lambda stmt, *_a, **_kw: stmt,
        ):
            resolver = query._create_auto_resolver(post_type, return_list=True)
            resolver(None, info)

        executed_stmt = session.execute.call_args.args[0]
        sql = str(executed_stmt.compile()).lower()
        assert "posts.title" in sql and "where" in sql


# ---------------------------------------------------------------------------
# Session compatibility: sync (WSGI/ASGI) and async (ASGI + AsyncSession)
# ---------------------------------------------------------------------------


class TestSessionCompat:
    """End-to-end tests that drive graphql_sync and graphql to confirm the
    auto-resolver is compatible with both sync and async execution paths."""

    def test_graphql_sync_executes_with_sync_session(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])
        schema = make_executable_schema(
            TYPE_DEFS, [query, user_type, post_type, tag_type]
        )

        rows = [
            Mock(id=1, username="alice", posts=[], spec=["id", "username", "posts"])
        ]
        session = _make_sync_session(scalar_all=rows)

        from graphql import graphql_sync

        result = graphql_sync(
            schema,
            "{ users { id username } }",
            context_value={"session": session},
        )

        assert result.errors is None
        assert result.data == {"users": [{"id": "1", "username": "alice"}]}

    @pytest.mark.asyncio
    async def test_graphql_async_executes_with_sync_session(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])
        schema = make_executable_schema(
            TYPE_DEFS, [query, user_type, post_type, tag_type]
        )

        rows = [Mock(id=2, username="bob", posts=[], spec=["id", "username", "posts"])]
        session = _make_sync_session(scalar_all=rows)

        from graphql import graphql

        result = await graphql(
            schema,
            "{ users { id username } }",
            context_value={"session": session},
        )

        assert result.errors is None
        assert result.data == {"users": [{"id": "2", "username": "bob"}]}

    @pytest.mark.asyncio
    async def test_graphql_async_executes_with_async_session(self, models):
        user_type, post_type, tag_type = _make_object_types(models)
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])
        schema = make_executable_schema(
            TYPE_DEFS, [query, user_type, post_type, tag_type]
        )

        rows = [
            Mock(id=3, username="carol", posts=[], spec=["id", "username", "posts"])
        ]
        session = _make_async_session(scalar_all=rows)

        from graphql import graphql

        result = await graphql(
            schema,
            "{ users { id username } }",
            context_value={"session": session},
        )

        assert result.errors is None
        assert result.data == {"users": [{"id": "3", "username": "carol"}]}
