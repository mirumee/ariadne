from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from graphql import GraphQLError, parse
from graphql.language import FragmentDefinitionNode, OperationDefinitionNode
from sqlalchemy.orm import (
    class_mapper,
    joinedload,
    lazyload,
    selectinload,
    subqueryload,
)

from ariadne.contrib.sqlalchemy import SQLAlchemyObjectType
from ariadne.contrib.sqlalchemy.utils import (
    DepthLimit,
    _build_options,
    _resolve_load_option,
    auto_eager_load,
)


def _info_for(query_string: str, root_field: str) -> SimpleNamespace:
    """Mimic the `info` object passed to a resolver for `root_field`.

    Picks the matching FieldNodes out of the parsed operation's selection set
    and builds a fragments dict from any FragmentDefinitionNode in the document,
    matching what graphql-core hands the resolver at runtime.
    """
    document = parse(query_string)
    operation = next(
        d for d in document.definitions if isinstance(d, OperationDefinitionNode)
    )
    field_nodes = [
        node
        for node in operation.selection_set.selections
        if node.name.value == root_field
    ]
    fragments = {
        d.name.value: d
        for d in document.definitions
        if isinstance(d, FragmentDefinitionNode)
    }
    return SimpleNamespace(field_nodes=field_nodes, fragments=fragments)


def _selections(query_string: str, root_field: str):
    """Return the inner selection set's selections for `root_field`."""
    info = _info_for(query_string, root_field)
    return info.field_nodes[0].selection_set.selections


# ---------------------------------------------------------------------------
# _resolve_load_option
# ---------------------------------------------------------------------------


class TestResolveLoadOption:
    def test_defaults_to_selectinload_for_collections(self, models):
        mapper = class_mapper(models["Post"])
        rel = mapper.relationships["tags"]

        opt = _resolve_load_option(mapper, "tags", None, rel, load_path=None)

        assert "Post.tags" in str(opt.path)
        # selectinload emits a separate IN query; joinedload would have rolled
        # the relationship into the parent path in a single statement. We can
        # tell them apart by patching and re-running.
        with patch(
            "ariadne.contrib.sqlalchemy.utils.selectinload",
            wraps=selectinload,
        ) as sel:
            _resolve_load_option(mapper, "tags", None, rel, load_path=None)
        sel.assert_called_once()

    def test_defaults_to_joinedload_for_scalars(self, models):
        mapper = class_mapper(models["Post"])
        rel = mapper.relationships["author"]

        with patch(
            "ariadne.contrib.sqlalchemy.utils.joinedload",
            wraps=joinedload,
        ) as joined:
            _resolve_load_option(mapper, "author", None, rel, load_path=None)
        joined.assert_called_once()

    def test_uses_explicit_strategy(self, models):
        mapper = class_mapper(models["Post"])
        rel = mapper.relationships["tags"]
        strategy = Mock(side_effect=lambda attr: selectinload(attr))
        strategy.__name__ = "selectinload"

        _resolve_load_option(mapper, "tags", strategy, rel, load_path=None)

        strategy.assert_called_once()
        # The single positional arg should be the InstrumentedAttribute
        passed = strategy.call_args.args[0]
        assert passed is models["Post"].tags

    def test_chains_onto_load_path(self, models):
        mapper = class_mapper(models["Post"])
        rel_tags = mapper.relationships["tags"]

        root = _resolve_load_option(mapper, "tags", selectinload, rel_tags, None)

        tag_mapper = class_mapper(models["Tag"])
        rel_posts = tag_mapper.relationships["posts"]
        nested = _resolve_load_option(
            tag_mapper, "posts", selectinload, rel_posts, load_path=root
        )

        # Nested option's path includes both legs of the relationship chain.
        path_str = str(nested.path)
        assert "Post.tags" in path_str
        assert "Tag.posts" in path_str


# ---------------------------------------------------------------------------
# auto_eager_load
# ---------------------------------------------------------------------------


class TestAutoEagerLoad:
    def test_returns_query_unchanged_when_no_field_nodes(self, models):
        query = Mock(name="query")
        info = SimpleNamespace(field_nodes=[])

        result = auto_eager_load(query, info, models["Post"])

        assert result is query
        query.options.assert_not_called()

    def test_returns_query_unchanged_when_root_field_has_no_selections(self, models):
        """A scalar root field has no selection set, so there is nothing to
        eager-load - the query must come back untouched."""
        query = Mock(name="query")
        # `ping` would be a scalar root field with no inner selection set.
        document = parse("query Q { ping }")
        operation = document.definitions[0]
        info = SimpleNamespace(field_nodes=list(operation.selection_set.selections))

        result = auto_eager_load(query, info, models["Post"])

        assert result is query
        query.options.assert_not_called()

    def test_passes_options_to_query(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { title } }", "posts")

        auto_eager_load(query, info, models["Post"])

        query.options.assert_called_once()
        # At minimum, scalar `title` should produce one load_only option.
        assert len(query.options.call_args.args) >= 1

    def test_emits_load_only_for_scalar_fields(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { id title } }", "posts")

        with patch(
            "ariadne.contrib.sqlalchemy.utils.load_only", wraps=lambda *a: a
        ) as lo:
            auto_eager_load(query, info, models["Post"])

        lo.assert_called_once()
        loaded_attrs = {attr.key for attr in lo.call_args.args}
        # Includes the requested scalars plus the FK column needed by any
        # relationship resolver fall-back.
        assert {"id", "title"}.issubset(loaded_attrs)
        assert "author_id" in loaded_attrs

    def test_includes_fk_columns_in_load_only(self, models):
        """Even if the GraphQL selection only asks for a single scalar, the
        FK columns of every relationship on that mapper must be loaded so the
        DataLoader fallback can fetch related rows by FK."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { title } }", "posts")

        with patch(
            "ariadne.contrib.sqlalchemy.utils.load_only", wraps=lambda *a: a
        ) as lo:
            auto_eager_load(query, info, models["Post"])

        loaded = {attr.key for attr in lo.call_args.args}
        assert "author_id" in loaded

    def test_no_load_only_when_only_relationships_selected(self, models):
        """If the selection contains only relationships (no scalar columns),
        nothing is loaded via `load_only` - we just attach the relationship
        loaders. This means FKs are not pre-loaded either."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { id } } }", "posts")

        with patch(
            "ariadne.contrib.sqlalchemy.utils.load_only", wraps=lambda *a: a
        ) as lo:
            auto_eager_load(query, info, models["Post"])

        # Only the inner Tag's `id` triggers load_only - never the outer Post.
        for call in lo.call_args_list:
            keys = {attr.key for attr in call.args}
            assert "title" not in keys

    def test_default_strategy_for_collection_relationship(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { id } } }", "posts")

        with patch(
            "ariadne.contrib.sqlalchemy.utils.selectinload",
            wraps=selectinload,
        ) as sel:
            auto_eager_load(query, info, models["Post"])

        # `tags` is a collection -> selectinload by default
        sel.assert_called()

    def test_default_strategy_for_scalar_relationship(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { author { id } } }", "posts")

        with patch(
            "ariadne.contrib.sqlalchemy.utils.joinedload",
            wraps=joinedload,
        ) as joined:
            auto_eager_load(query, info, models["Post"])

        # `author` is a many-to-one scalar -> joinedload by default
        joined.assert_called()

    def test_explicit_strategy_overrides_default(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { id } } }", "posts")
        strategy = Mock(side_effect=subqueryload)
        strategy.__name__ = "subqueryload"

        auto_eager_load(query, info, models["Post"], strategies={"tags": strategy})

        strategy.assert_called_once()

    def test_aliases_translate_graphql_field_to_db_attr(self, models):
        query = Mock(name="query")
        # GraphQL exposes `myTitle`; map it to the `title` column on Post.
        info = _info_for("query Q { posts { myTitle } }", "posts")

        with patch(
            "ariadne.contrib.sqlalchemy.utils.load_only", wraps=lambda *a: a
        ) as lo:
            auto_eager_load(query, info, models["Post"], aliases={"myTitle": "title"})

        loaded = {attr.key for attr in lo.call_args.args}
        assert "title" in loaded

    def test_recurses_into_nested_selections(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { name posts { id } } } }", "posts")

        auto_eager_load(query, info, models["Post"])

        opts = query.options.call_args.args
        joined = " | ".join(str(o.path) for o in opts)
        assert "Post.tags" in joined
        assert "Tag.posts" in joined

    def test_aliases_only_apply_at_root_without_registry(self, models):
        """`auto_eager_load`'s `aliases` argument applies to the root model
        only. Nested types fall back to no aliases unless a `type_registry`
        provides per-type config."""
        query = Mock(name="query")
        # Root selection uses `myTitle` (alias) and a relationship; the nested
        # tag selection uses unaliased `name`.
        info = _info_for("query Q { posts { myTitle tags { name } } }", "posts")

        auto_eager_load(query, info, models["Post"], aliases={"myTitle": "title"})

        query.options.assert_called_once()

    def test_uses_type_registry_for_nested_type_aliases(self, models):
        """A type_registry entry for the nested type supplies that type's
        aliases - the parent's aliases do not leak into the recursion."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { my_name } } }", "posts")

        post_ot = SQLAlchemyObjectType("Post", models["Post"])
        tag_ot = SQLAlchemyObjectType("Tag", models["Tag"], aliases={"my_name": "name"})
        registry = {models["Post"]: post_ot, models["Tag"]: tag_ot}

        from ariadne.contrib.sqlalchemy.utils import _build_options

        with patch(
            "ariadne.contrib.sqlalchemy.utils._build_options",
            wraps=_build_options,
        ) as build_mock:
            auto_eager_load(query, info, models["Post"], type_registry=registry)

        # Find the recursive call entered for the Tag mapper.
        tag_calls = [
            c for c in build_mock.call_args_list if c.args[0].class_ is models["Tag"]
        ]
        assert tag_calls, "expected a recursive call for the Tag mapper"
        # Aliases dict at the Tag level is sourced from the Tag's own config.
        passed_aliases = tag_calls[0].args[3]
        assert passed_aliases == {"my_name": "name"}

    def test_child_type_absent_from_registry_uses_empty_strategies(self, models):
        """When a child type is not in type_registry, its strategies must default
        to {} — not inherit the parent's strategies dict."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { posts { id } } } }", "posts")

        post_ot = SQLAlchemyObjectType(
            "Post", models["Post"], strategies={"tags": joinedload}
        )
        # Tag is intentionally absent from the registry.
        registry = {models["Post"]: post_ot}

        with patch(
            "ariadne.contrib.sqlalchemy.utils._build_options",
            wraps=_build_options,
        ) as build_mock:
            auto_eager_load(query, info, models["Post"], type_registry=registry)

        tag_calls = [
            c for c in build_mock.call_args_list if c.args[0].class_ is models["Tag"]
        ]
        assert tag_calls, "expected a recursive call for the Tag mapper"
        passed_strategies = tag_calls[0].args[2]
        assert passed_strategies == {}, (
            "parent strategies must not leak into an unregistered child type"
        )

    def test_uses_child_strategy_from_registry(self, models):
        """A nested type's `strategies` dict is what controls how its own
        relationships load. The strategy's `__name__` is what matters at
        nested levels - the option is chained via `load_path.<name>(attr)`."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { posts { id } } } }", "posts")

        post_ot = SQLAlchemyObjectType("Post", models["Post"])
        # Use a real loader so chaining via `load_path.subqueryload` works.
        tag_ot = SQLAlchemyObjectType(
            "Tag", models["Tag"], strategies={"posts": subqueryload}
        )
        registry = {models["Post"]: post_ot, models["Tag"]: tag_ot}

        with patch(
            "ariadne.contrib.sqlalchemy.utils._resolve_load_option",
            wraps=_resolve_load_option,
        ) as resolve_mock:
            auto_eager_load(query, info, models["Post"], type_registry=registry)

        # The Tag-level resolution must receive the Tag's strategy (`subqueryload`),
        # rather than falling back to the default `selectinload` for collections.
        tag_calls = [c for c in resolve_mock.call_args_list if c.args[1] == "posts"]
        assert tag_calls, "expected a resolve call for Tag.posts"
        assert tag_calls[0].args[2] is subqueryload

    def test_child_type_max_depth_narrows_inherited_limit(self, models):
        """A child type's max_depth is inherited as min(parent_limit, child_limit).

        Post max_depth=100, Tag max_depth=3.
        Entering Tag reduces the effective limit to min(100, 3) = 3, so the
        traversal is capped at depth 3 regardless of Post's generous limit.
        """
        query = Mock(name="query")
        # 8 nesting levels: Post→Tag→Post→Tag→Post→Tag→Post→Tag→id
        # Tag would be entered 4 times, which exceeds its max_depth=3.
        info = _info_for(
            "query Q { posts { tags { posts { tags { posts { tags { posts { tags { id"
            " } } } } } } } } }",
            "posts",
        )

        post_ot = SQLAlchemyObjectType("Post", models["Post"], max_depth=100)
        tag_ot = SQLAlchemyObjectType("Tag", models["Tag"], max_depth=3)
        registry = {models["Post"]: post_ot, models["Tag"]: tag_ot}

        with pytest.raises(GraphQLError, match="max_depth"):
            auto_eager_load(query, info, models["Post"], type_registry=registry)

    def test_max_depth_from_registry_raises_graphql_error(self, models):
        """The root type's max_depth from the registry is the global depth limit.
        Any nesting beyond it raises regardless of which type is encountered."""
        query = Mock(name="query")
        info = _info_for(
            # 4 total levels: posts(1) -> tags(2) -> posts(3) -> tags(4)
            "query Q { posts { tags { posts { tags { id } } } } }",
            "posts",
        )

        post_ot = SQLAlchemyObjectType("Post", models["Post"], max_depth=1)
        tag_ot = SQLAlchemyObjectType("Tag", models["Tag"], max_depth=1)
        registry = {models["Post"]: post_ot, models["Tag"]: tag_ot}

        with pytest.raises(GraphQLError, match="max_depth"):
            auto_eager_load(query, info, models["Post"], type_registry=registry)

    def test_default_max_depth_three_allows_three_levels(self, models):
        """With the default max_depth=3, a three-level query loads without raising."""
        query = Mock(name="query")
        info = _info_for(
            "query Q { posts { tags { posts { id } } } }",
            "posts",
        )

        auto_eager_load(query, info, models["Post"])

        query.options.assert_called_once()

    def test_max_depth_error_message_includes_depth(self, models):
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { posts { id } } } }", "posts")

        post_ot = SQLAlchemyObjectType("Post", models["Post"], max_depth=1)
        registry = {models["Post"]: post_ot}

        with pytest.raises(GraphQLError) as exc_info:
            auto_eager_load(query, info, models["Post"], type_registry=registry)

        assert "max_depth=1" in str(exc_info.value)
        assert "Post" in str(exc_info.value)

    def test_error_attributes_limit_to_narrowing_child_type(self, models):
        """When a child type's max_depth is stricter, it is named in the error."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { posts { id } } } }", "posts")

        post_ot = SQLAlchemyObjectType("Post", models["Post"], max_depth=5)
        tag_ot = SQLAlchemyObjectType("Tag", models["Tag"], max_depth=1)
        registry = {models["Post"]: post_ot, models["Tag"]: tag_ot}

        with pytest.raises(GraphQLError) as exc_info:
            auto_eager_load(query, info, models["Post"], type_registry=registry)

        message = str(exc_info.value)
        assert "max_depth=1" in message
        assert "Tag" in message
        assert "Post" not in message

    def test_unknown_graphql_field_is_ignored(self, models):
        """Selecting a GraphQL field that doesn't exist on the SQLAlchemy
        model (no column, no relationship, no alias) just gets skipped."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { id ghostField } }", "posts")

        auto_eager_load(query, info, models["Post"])

        query.options.assert_called_once()


class TestMaxDepthForwarding:
    def test_custom_max_depth_is_enforced(self, models):
        """max_depth=1 must raise GraphQLError at total depth 2."""
        query = Mock(name="query")
        info = _info_for("query Q { posts { tags { posts { id } } } }", "posts")

        with pytest.raises(GraphQLError, match="max_depth"):
            auto_eager_load(query, info, models["Post"], max_depth=1)


class TestBuildOptions:
    def test_returns_empty_list_for_empty_selection(self, models):
        mapper = class_mapper(models["Post"])
        opts = _build_options(
            mapper, [], {}, {}, DepthLimit(3, "Post"), type_registry={}
        )
        assert opts == []

    def test_supports_lazyload_strategy_via_dunder_name(self, models):
        """The chaining branch (`getattr(strategy, '__name__')`) requires the
        strategy to expose `__name__`. The shipped SQLAlchemy strategies all
        do - sanity-check with `lazyload`."""
        mapper = class_mapper(models["Post"])
        selections = _selections("query Q { posts { tags { posts { id } } } }", "posts")

        opts = _build_options(
            mapper,
            selections,
            {"tags": lazyload, "posts": lazyload},
            {},
            DepthLimit(3, "Post"),
            type_registry={},
        )

        assert any("Post.tags" in str(o.path) for o in opts)
