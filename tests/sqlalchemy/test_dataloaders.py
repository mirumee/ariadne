from unittest.mock import AsyncMock, Mock

import pytest
from aiodataloader import DataLoader
from sqlalchemy import inspect as sa_inspect

from ariadne.contrib.sqlalchemy.dataloaders import (
    LoaderRegistry,
    SQLAlchemyDataLoader,
)


def get_relation(model, name):
    return sa_inspect(model).relationships[name]


def make_session(rows):
    """Build a sync session whose `execute(stmt).all()` returns `rows`."""
    result = Mock()
    result.all.return_value = rows
    session = Mock()
    session.execute.return_value = result
    return session


def make_async_session(rows):
    """Build an async-style session: `execute(...)` returns an awaitable."""
    result = Mock()
    result.all.return_value = rows
    session = Mock()
    session.execute = AsyncMock(return_value=result)
    return session


# ---------------------------------------------------------------------------
# SQLAlchemyDataLoader.__init__
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSQLAlchemyDataLoaderInit:
    async def test_one_to_many_resolves_local_and_remote_columns(self, models):
        session = Mock(name="session")
        relation = get_relation(models["User"], "posts")
        loader = SQLAlchemyDataLoader(session, relation)

        assert loader.session is session
        assert loader.relation_prop is relation
        assert loader.target_model is models["Post"]
        assert loader.is_list is True
        assert loader.secondary is None
        assert loader.local_cols == ["id"]
        assert loader.remote_cols == ["author_id"]

    async def test_many_to_one_marks_uselist_false(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["Post"], "author"))

        assert loader.is_list is False
        assert loader.target_model is models["User"]
        assert loader.secondary is None
        assert loader.local_cols == ["author_id"]
        assert loader.remote_cols == ["id"]

    async def test_many_to_many_uses_secondary_synchronize_pairs(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["Post"], "tags"))

        assert loader.is_list is True
        assert loader.secondary is models["post_tags"]
        # M2M follows synchronize_pairs (parent -> secondary):
        # `local_cols` is the parent PK, `remote_cols` is the secondary's
        # parent-side FK column - the column we filter and group on.
        assert loader.local_cols == ["id"]
        assert loader.remote_cols == ["post_id"]

    async def test_many_to_many_reverse_side(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["Tag"], "posts"))

        assert loader.is_list is True
        assert loader.secondary is models["post_tags"]
        assert loader.local_cols == ["id"]
        assert loader.remote_cols == ["tag_id"]

    async def test_default_cache_is_enabled(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["User"], "posts"))
        assert loader.cache is True

    async def test_cache_can_be_disabled(self, models):
        loader = SQLAlchemyDataLoader(
            Mock(), get_relation(models["User"], "posts"), cache=False
        )
        assert loader.cache is False

    async def test_loader_is_an_aiodataloader(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["User"], "posts"))
        assert isinstance(loader, DataLoader)

    async def test_composite_key_relationship(self, composite_key_models):
        loader = SQLAlchemyDataLoader(
            Mock(), get_relation(composite_key_models["Region"], "cities")
        )

        assert loader.is_list is True
        assert sorted(loader.local_cols) == sorted(["country", "code"])
        assert sorted(loader.remote_cols) == sorted(["country", "region_code"])


# ---------------------------------------------------------------------------
# SQLAlchemyDataLoader.get_query
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetQuery:
    def _compile(self, stmt):
        return str(stmt.compile(compile_kwargs={"literal_binds": True})).lower()

    async def test_simple_relation_uses_in_clause(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["User"], "posts"))

        sql = self._compile(loader.get_query([1, 2]))

        assert "from posts" in sql
        assert "author_id in" in sql
        assert "1" in sql and "2" in sql

    async def test_simple_relation_unwraps_tuple_keys(self, models):
        """The dataloader accepts both scalars and 1-tuples for single-column
        relationships; tuples get flattened into a scalar IN clause."""
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["User"], "posts"))

        sql = self._compile(loader.get_query([(1,), (2,)]))

        # No tuple comparison - regular `IN (1, 2)`.
        assert "in (1, 2)" in sql

    async def test_many_to_one_filters_target_pk(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["Post"], "author"))

        sql = self._compile(loader.get_query([1, 2]))

        assert "from users" in sql
        assert "users.id in" in sql

    async def test_secondary_query_joins_through_secondary(self, models):
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["Post"], "tags"))

        sql = self._compile(loader.get_query([10, 12]))

        assert "from tags" in sql
        assert "join post_tags" in sql
        # The dataloader filters on the secondary's parent-side FK column.
        assert "post_tags.post_id in" in sql

    async def test_composite_key_query_uses_tuple_in(self, composite_key_models):
        loader = SQLAlchemyDataLoader(
            Mock(), get_relation(composite_key_models["Region"], "cities")
        )

        sql = self._compile(loader.get_query([("US", "CA"), ("UK", "LD")]))

        # tuple_(...).in_(...) renders as a multi-column IN.
        assert "in (" in sql
        assert "'us'" in sql and "'ca'" in sql

    async def test_filter_columns_are_appended_as_result_columns(self, models):
        """The dataloader appends filter columns so it can group rows by key."""
        loader = SQLAlchemyDataLoader(Mock(), get_relation(models["User"], "posts"))

        stmt = loader.get_query([1])
        assert any("author_id" in str(col) for col in stmt.selected_columns)


# ---------------------------------------------------------------------------
# SQLAlchemyDataLoader.batch_load_fn (sync session)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBatchLoadOneToMany:
    async def test_groups_results_by_filter_column(self, models):
        # Rows: (post_obj, author_id) - the dataloader groups by author_id.
        post_a1 = Mock(name="post-a1")
        post_a2 = Mock(name="post-a2")
        post_b1 = Mock(name="post-b1")

        session = make_session([(post_a1, 1), (post_a2, 1), (post_b1, 2)])

        loader = SQLAlchemyDataLoader(session, get_relation(models["User"], "posts"))
        result = await loader.batch_load_fn([1, 2, 3])

        assert result == [[post_a1, post_a2], [post_b1], []]
        # The session was driven exactly once - that's the whole point of
        # batching.
        session.execute.assert_called_once()

    async def test_preserves_input_order(self, models):
        post_a = Mock(name="post-a")
        post_b = Mock(name="post-b")
        session = make_session([(post_a, 1), (post_b, 2)])

        loader = SQLAlchemyDataLoader(session, get_relation(models["User"], "posts"))
        result = await loader.batch_load_fn([2, 3, 1])

        assert result == [[post_b], [], [post_a]]

    async def test_load_many_dispatches_one_batch(self, models):
        """Public DataLoader.load_many funnels through a single batch_load_fn
        call - this is the contract Ariadne resolvers rely on."""
        post_a = Mock()
        post_b = Mock()
        session = make_session([(post_a, 1), (post_b, 2)])

        loader = SQLAlchemyDataLoader(session, get_relation(models["User"], "posts"))
        groups = await loader.load_many([1, 2, 3])

        assert groups == [[post_a], [post_b], []]
        session.execute.assert_called_once()


@pytest.mark.asyncio
class TestBatchLoadManyToOne:
    async def test_returns_single_object_per_key(self, models):
        alice = Mock(name="alice")
        bob = Mock(name="bob")
        session = make_session([(alice, 1), (bob, 2)])

        loader = SQLAlchemyDataLoader(session, get_relation(models["Post"], "author"))
        result = await loader.batch_load_fn([1, 2])

        assert result == [alice, bob]

    async def test_returns_none_when_no_match(self, models):
        alice = Mock(name="alice")
        session = make_session([(alice, 1)])

        loader = SQLAlchemyDataLoader(session, get_relation(models["Post"], "author"))
        # Author id 999 has no row in the result set.
        result = await loader.batch_load_fn([1, 999])

        assert result == [alice, None]


@pytest.mark.asyncio
class TestBatchLoadManyToMany:
    async def test_groups_through_secondary(self, models):
        # Rows for Post.tags grouped by post_tags.post_id (the filter column).
        python_tag = Mock(name="python")
        graphql_tag = Mock(name="graphql")
        session = make_session(
            [
                (python_tag, 10),
                (graphql_tag, 10),
                (python_tag, 11),
                (graphql_tag, 12),
            ]
        )

        loader = SQLAlchemyDataLoader(session, get_relation(models["Post"], "tags"))
        result = await loader.batch_load_fn([10, 11, 12, 13])

        assert result == [
            [python_tag, graphql_tag],
            [python_tag],
            [graphql_tag],
            [],
        ]

    async def test_reverse_side_groups_correctly(self, models):
        """Tag.posts goes through the same secondary in the opposite direction
        - the dataloader should group by `tag_id`."""
        post_10 = Mock(name="post10")
        post_11 = Mock(name="post11")
        post_12 = Mock(name="post12")
        session = make_session(
            [
                (post_10, 1),
                (post_11, 1),
                (post_10, 2),
                (post_12, 2),
            ]
        )

        loader = SQLAlchemyDataLoader(session, get_relation(models["Tag"], "posts"))
        result = await loader.batch_load_fn([1, 2, 3])

        assert result == [[post_10, post_11], [post_10, post_12], []]


@pytest.mark.asyncio
class TestBatchLoadCompositeKeys:
    async def test_groups_by_composite_key_tuple(self, composite_key_models):
        sf = Mock(name="sf")
        la = Mock(name="la")
        buffalo = Mock(name="buf")
        london = Mock(name="ldn")

        # Rows: (city, country, region_code) - two filter columns.
        session = make_session(
            [
                (sf, "US", "CA"),
                (la, "US", "CA"),
                (buffalo, "US", "NY"),
                (london, "UK", "LD"),
            ]
        )

        loader = SQLAlchemyDataLoader(
            session, get_relation(composite_key_models["Region"], "cities")
        )
        result = await loader.batch_load_fn(
            [("US", "CA"), ("US", "NY"), ("UK", "LD"), ("FR", "PA")]
        )

        assert result == [[sf, la], [buffalo], [london], []]


# ---------------------------------------------------------------------------
# SQLAlchemyDataLoader.batch_load_fn (async session path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBatchLoadAsyncSession:
    async def test_awaits_async_session_execute(self, models):
        """When `session.execute(...)` returns an awaitable (as AsyncSession
        does), the dataloader awaits it before consuming `.all()`."""
        post = Mock(name="post")
        async_session = make_async_session([(post, 1)])

        loader = SQLAlchemyDataLoader(
            async_session, get_relation(models["User"], "posts")
        )
        result = await loader.batch_load_fn([1])

        async_session.execute.assert_awaited_once()
        assert result == [[post]]


# ---------------------------------------------------------------------------
# LoaderRegistry
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
class TestLoaderRegistry:
    async def test_caches_loader_per_relationship(self, models):
        registry = LoaderRegistry(Mock(name="session"))
        relation = get_relation(models["User"], "posts")

        a = registry.get_loader(relation)
        b = registry.get_loader(relation)

        assert a is b
        assert isinstance(a, SQLAlchemyDataLoader)

    async def test_passes_session_to_loader(self, models):
        session = Mock(name="session")
        registry = LoaderRegistry(session)

        loader = registry.get_loader(get_relation(models["User"], "posts"))

        assert loader.session is session

    async def test_distinct_relationships_get_distinct_loaders(self, models):
        registry = LoaderRegistry(Mock())

        users_posts = registry.get_loader(get_relation(models["User"], "posts"))
        post_author = registry.get_loader(get_relation(models["Post"], "author"))

        assert users_posts is not post_author
        assert users_posts.target_model is models["Post"]
        assert post_author.target_model is models["User"]

    async def test_custom_loader_class_is_keyed_separately(self, models):
        class CustomLoader(SQLAlchemyDataLoader):
            pass

        registry = LoaderRegistry(Mock())
        relation = get_relation(models["User"], "posts")

        default = registry.get_loader(relation)
        custom = registry.get_loader(relation, loader_class=CustomLoader)

        assert default is not custom
        assert type(default) is SQLAlchemyDataLoader
        assert type(custom) is CustomLoader
        # Subsequent lookups for the same (relation, class) hit the cache.
        assert registry.get_loader(relation, loader_class=CustomLoader) is custom
