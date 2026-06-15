from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from graphql import (
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import selectinload

from ariadne import make_executable_schema
from ariadne.contrib.sqlalchemy import (
    LoaderRegistry,
    SQLAlchemyDataLoader,
    SQLAlchemyObjectType,
    SQLAlchemyQueryType,
)


def get_relation(model, name):
    return sa_inspect(model).relationships[name]


# ---------------------------------------------------------------------------
# Construction defaults & overrides
# ---------------------------------------------------------------------------


class TestInit:
    def test_defaults(self, models):
        ot = SQLAlchemyObjectType("User", models["User"])

        assert ot.name == "User"
        assert ot.model is models["User"]
        assert ot.aliases == {}
        assert ot.strategies == {}
        assert ot.max_depth == 3

    def test_dict_aliases_are_stored_directly(self, models):
        aliases = {"my_post_id": "post_id"}
        ot = SQLAlchemyObjectType("Post", models["Post"], aliases=aliases)

        assert ot.aliases == aliases

    def test_strategies_and_max_depth_are_stored(self, models):
        ot = SQLAlchemyObjectType(
            "Post",
            models["Post"],
            strategies={"author": selectinload, "tags": selectinload},
            max_depth=4,
        )

        assert ot.strategies == {"author": selectinload, "tags": selectinload}
        assert ot.max_depth == 4


class TestBindAutoResolvers:
    def _build_schema(self, *bindables):
        type_defs = """
            type Query {
                users: [User!]!
                posts: [Post!]!
                tags: [Tag!]!
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
        return make_executable_schema(type_defs, list(bindables))

    def test_relationship_fields_get_auto_resolvers(self, models):
        user_type = SQLAlchemyObjectType("User", models["User"])
        post_type = SQLAlchemyObjectType("Post", models["Post"])
        tag_type = SQLAlchemyObjectType("Tag", models["Tag"])
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        schema = self._build_schema(query, user_type, post_type, tag_type)

        # Every relationship field has a resolver bound to the GraphQL field.
        post = schema.type_map["Post"]
        assert post.fields["author"].resolve is not None
        assert post.fields["tags"].resolve is not None

        user = schema.type_map["User"]
        assert user.fields["posts"].resolve is not None

        # Auto-resolvers also get registered on the bindable's `_resolvers`
        # dict so that any subsequent rebind sees them.
        assert "author" in post_type._resolvers
        assert "tags" in post_type._resolvers
        assert "posts" in user_type._resolvers

    def test_existing_resolver_is_not_overwritten_by_auto_resolver(self, models):
        post_type = SQLAlchemyObjectType("Post", models["Post"])

        # User-defined resolver registered before bind_to_schema runs.
        @post_type.field("author")
        def custom_author(*_):  # pragma: no cover - identity check only
            return None

        user_type = SQLAlchemyObjectType("User", models["User"])
        tag_type = SQLAlchemyObjectType("Tag", models["Tag"])
        query = SQLAlchemyQueryType([user_type, post_type, tag_type])

        self._build_schema(query, user_type, post_type, tag_type)

        # The custom resolver wins - auto-binding skips fields already in
        # `_resolvers`.
        assert post_type._resolvers["author"] is custom_author

    def test_alias_for_field_not_in_schema_is_skipped(self, models):
        post_type = SQLAlchemyObjectType(
            "Post", models["Post"], aliases={"missing": "title"}
        )

        gql_type = GraphQLObjectType(
            "Post",
            {
                "title": GraphQLField(GraphQLString),
                "author": GraphQLField(GraphQLString),
                "tags": GraphQLField(GraphQLList(GraphQLString)),
            },
        )
        schema = GraphQLSchema(types=[gql_type])
        post_type.bind_to_schema(schema)

        assert "missing" not in post_type._resolvers

    def test_relationship_not_in_schema_is_skipped(self, models):
        # Schema exposes Post but omits the `tags` field - auto-binding must
        # not register a resolver for a field the schema doesn't define.
        gql_type = GraphQLObjectType(
            "Post",
            {
                "title": GraphQLField(GraphQLString),
                "author": GraphQLField(GraphQLString),
            },
        )
        schema = GraphQLSchema(types=[gql_type])
        post_type = SQLAlchemyObjectType("Post", models["Post"])
        post_type.bind_to_schema(schema)

        assert "tags" not in post_type._resolvers
        assert "author" in post_type._resolvers

    def test_missing_type_in_schema_raises(self, models):
        schema = GraphQLSchema(
            query=GraphQLObjectType(
                "Query", {"x": GraphQLField(GraphQLNonNull(GraphQLInt))}
            ),
        )
        post_type = SQLAlchemyObjectType("Post", models["Post"])

        with pytest.raises(ValueError, match="Post"):
            post_type.bind_to_schema(schema)


class TestGetLoaderRegistryFromContext:
    def test_returns_value_from_default_key(self):
        registry = Mock(name="registry")
        assert (
            SQLAlchemyObjectType.get_loader_registry_from_context(
                {"loader_registry": registry}
            )
            is registry
        )

    def test_missing_key_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="loader_registry"):
            SQLAlchemyObjectType.get_loader_registry_from_context({})

    def test_subclass_can_override_lookup(self, models):
        class MyObjectType(SQLAlchemyObjectType):
            @staticmethod
            def get_loader_registry_from_context(context):
                return context["request"].state.loaders

        registry = Mock(name="registry")
        context = {"request": SimpleNamespace(state=SimpleNamespace(loaders=registry))}

        assert MyObjectType.get_loader_registry_from_context(context) is registry


class TestGetBaseQuery:
    def test_returns_select_for_model(self, models):
        ot = SQLAlchemyObjectType("Post", models["Post"])
        stmt = ot.get_base_query(info=Mock())

        # `select(Post)` renders to `SELECT ... FROM posts`.
        sql = str(stmt.compile()).lower()
        assert "from posts" in sql


@pytest.mark.asyncio
class TestRelationResolver:
    def _make_resolver(self, post_type, relation):
        return post_type._create_relation_resolver(relation)

    async def test_returns_preloaded_value_without_touching_loader(self, models):
        """If the relationship is already populated on the ORM instance (e.g.
        via `selectinload`), the resolver must read it directly and not
        consult the registry - that's the whole point of the auto_eager_load
        fast path."""
        post_type = SQLAlchemyObjectType("Post", models["Post"])
        relation = get_relation(models["Post"], "author")
        resolver = self._make_resolver(post_type, relation)

        author = SimpleNamespace(username="alice")
        # Mimic SQLAlchemy populating the relationship: the attribute is
        # present on the instance's __dict__.
        post = SimpleNamespace(author=author, author_id=1)

        registry = Mock(spec=LoaderRegistry)
        info = SimpleNamespace(context={"loader_registry": registry})

        result = await resolver(post, info)

        assert result is author
        registry.get_loader.assert_not_called()

    async def test_falls_through_to_loader_when_not_preloaded(self, models):
        """Manual resolvers return ORM rows with empty relationship state.
        The auto-bound resolver must look the relationship up via the
        per-request `LoaderRegistry`."""
        post_type = SQLAlchemyObjectType("Post", models["Post"])
        relation = get_relation(models["Post"], "author")
        resolver = self._make_resolver(post_type, relation)

        loader = Mock(spec=SQLAlchemyDataLoader)
        loader.load = Mock(return_value=_awaitable("alice"))
        registry = Mock(spec=LoaderRegistry)
        registry.get_loader.return_value = loader

        # __dict__ has the FK column but NOT the relationship attribute.
        post = SimpleNamespace(author_id=42)
        # Prune `author` from the namespace's auto-attributes so the
        # `relation.key in obj.__dict__` check in objects.py returns False.
        post.__dict__.pop("author", None)

        info = SimpleNamespace(context={"loader_registry": registry})
        result = await resolver(post, info)

        assert result == "alice"
        registry.get_loader.assert_called_once_with(relation)
        loader.load.assert_called_once_with(42)

    async def test_unwraps_single_column_key(self, models):
        """Single-column FK → loader is called with the scalar value, not a
        1-tuple. (`SQLAlchemyDataLoader` accepts both, but the relation
        resolver standardises on the unwrapped form.)"""
        post_type = SQLAlchemyObjectType("Post", models["Post"])
        relation = get_relation(models["Post"], "author")
        resolver = self._make_resolver(post_type, relation)

        loader = Mock(spec=SQLAlchemyDataLoader)
        loader.load = Mock(return_value=_awaitable(None))
        registry = Mock(spec=LoaderRegistry)
        registry.get_loader.return_value = loader

        post = SimpleNamespace(author_id=7)
        info = SimpleNamespace(context={"loader_registry": registry})
        await resolver(post, info)

        (key,) = loader.load.call_args.args
        assert key == 7  # not (7,)

    async def test_passes_composite_key_as_tuple(self, composite_key_models):
        """A composite-PK relationship must hand the loader the full tuple."""
        city_type = SQLAlchemyObjectType("City", composite_key_models["City"])
        relation = get_relation(composite_key_models["City"], "region")
        resolver = city_type._create_relation_resolver(relation)

        loader = Mock(spec=SQLAlchemyDataLoader)
        loader.load = Mock(return_value=_awaitable(None))
        registry = Mock(spec=LoaderRegistry)
        registry.get_loader.return_value = loader

        city = SimpleNamespace(country="US", region_code="CA")
        info = SimpleNamespace(context={"loader_registry": registry})
        await resolver(city, info)

        (key,) = loader.load.call_args.args
        assert isinstance(key, tuple) and len(key) == 2
        assert sorted(key) == sorted(("US", "CA"))

    async def test_uses_overridden_loader_registry_lookup(self, models):
        """`get_loader_registry_from_context` is the seam users override -
        the resolver must go through it, not read `context["loader_registry"]`
        directly."""

        class MyObjectType(SQLAlchemyObjectType):
            @staticmethod
            def get_loader_registry_from_context(context):
                return context["custom_loaders"]

        post_type = MyObjectType("Post", models["Post"])
        relation = get_relation(models["Post"], "author")
        resolver = post_type._create_relation_resolver(relation)

        loader = Mock(spec=SQLAlchemyDataLoader)
        loader.load = Mock(return_value=_awaitable("alice"))
        registry = Mock(spec=LoaderRegistry)
        registry.get_loader.return_value = loader

        post = SimpleNamespace(author_id=1)
        info = SimpleNamespace(context={"custom_loaders": registry})

        result = await resolver(post, info)

        assert result == "alice"
        registry.get_loader.assert_called_once_with(relation)


def _awaitable(value):
    async def _coro():
        return value

    return _coro()
