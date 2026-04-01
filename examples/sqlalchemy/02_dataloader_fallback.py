"""SQLAlchemy contrib example - Step 2: custom resolvers and DataLoaders.

This example demonstrates the two scenarios in which the DataLoader fallback
fires (see "Custom resolvers and DataLoaders" in the docs):

1. **A manual `@field` resolver returns ORM objects.** `publishedPosts` runs
   its own `select(Post).where(Post.is_published)` and returns the rows
   directly. They have empty `__dict__` for relationships, so resolving
   `author`/`tags` on them goes through `LoaderRegistry`.

2. **`Tag` is exposed in the schema but not registered with `SQLAlchemyQueryType`.**
   Only `user_type` and `post_type` are passed to the QueryType below;
   `tag_type` is defined (so its column/relationship resolvers exist on the
   `Tag` GraphQL type) but omitted from the QueryType registration.

What to watch in the SQL log (the engine runs with `echo=True`):

* `{ posts { title author { username } tags { name } } }` — Step 1 path. Even
  though `tag_type` isn't registered, `auto_eager_load` still applies
  `selectinload(Post.tags)` using *default* per-type config (no custom
  `max_depth`, `strategies`, or `aliases` for `Tag`). You'll see one SELECT
  for posts with the relationships joined/selectin'd in. **No DataLoader.**
  The practical effect of the missing registration is that `Tag`-specific
  config is ignored, not that the DataLoader fires.
* `{ publishedPosts { title author { username } tags { name } } }` — Step 2
  path. The manual resolver bypasses lookahead, so each requested
  relationship runs through the DataLoader: one batched `WHERE id IN (...)`
  for `author` and one joined query through `post_tags` for `tags`, on top
  of the manual `WHERE is_published` query.

Self-contained: a single file, an in-memory SQLite database, a synchronous
`Session` (the integration also accepts an `AsyncSession`, but two sibling
root resolvers race on its single connection - see the docs caveat).

Run with:

    uv run \
        --with "uvicorn[standard]" \
        --with ariadne \
        --with "sqlalchemy" \
        --with "aiodataloader" \
        uvicorn examples.sqlalchemy.02_dataloader_fallback:app --reload
"""

from contextlib import asynccontextmanager

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sqlalchemy import (
    SQLAlchemyDataLoaderExtension,
    SQLAlchemyObjectType,
    SQLAlchemyQueryType,
)

# --- Database --------------------------------------------------------------

Base = declarative_base()

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    is_published = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    posts = relationship("Post", secondary=post_tags, back_populates="tags")


engine = create_engine(
    "sqlite:///:memory:",
    echo=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        with SessionLocal() as session:
            request.state.session = session
            return await call_next(request)


def init_db() -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        alice = User(username="alice")
        bob = User(username="bob")
        python_tag = Tag(name="Python")
        graphql_tag = Tag(name="GraphQL")
        sqlalchemy_tag = Tag(name="SQLAlchemy")
        session.add_all(
            [
                alice,
                bob,
                python_tag,
                graphql_tag,
                sqlalchemy_tag,
                Post(
                    title="Hello, GraphQL",
                    author=alice,
                    tags=[python_tag, graphql_tag],
                    is_published=True,
                ),
                Post(
                    title="SQLAlchemy 2.0 tips",
                    author=bob,
                    tags=[graphql_tag, sqlalchemy_tag],
                    is_published=True,
                ),
                Post(
                    title="Draft notes",
                    author=alice,
                    tags=[python_tag],
                    is_published=False,
                ),
            ]
        )
        session.commit()


# --- GraphQL schema --------------------------------------------------------

type_defs = """
    type Query {
        # auto-resolved, no DataLoader.
        posts: [Post!]!

        # hit the DataLoader.
        publishedPosts: [Post!]!
    }

    type User {
        id: ID!
        username: String!
        posts: [Post!]!
    }

    type Post {
        id: ID!
        title: String!
        isPublished: Boolean!
        author: User!
        tags: [Tag!]!
    }

    type Tag {
        id: ID!
        name: String!
        posts: [Post!]!
    }
"""

user_type = SQLAlchemyObjectType("User", User)
post_type = SQLAlchemyObjectType("Post", Post, aliases={"isPublished": "is_published"})

# `tag_type` is intentionally NOT passed to `SQLAlchemyQueryType` below, even
# though `Tag` is reachable in the schema via `Post.tags`. Defining
# `tag_type` keeps the per-relationship resolvers on `Tag` (so `Tag.posts`
# still works), but auto_eager_load won't honour any per-type config you
# attach here when traversing into `Tag`.
tag_type = SQLAlchemyObjectType("Tag", Tag)

query_type = SQLAlchemyQueryType([user_type, post_type])


@query_type.field("publishedPosts")
def resolve_published_posts(_, info):
    session = info.context["session"]
    stmt = select(Post).where(Post.is_published)
    return session.execute(stmt).scalars().unique().all()


schema = make_executable_schema(type_defs, [query_type, user_type, post_type, tag_type])


# --- Context ---------------------------------------------------------------

# The `session` key is required for `SQLAlchemyQueryType`.
# `SQLAlchemyDataLoaderExtension` will automatically create the
# `loader_registry` in context for `SQLAlchemyObjectType`


async def get_context(request, _data):
    return {
        "request": request,
        "session": request.state.session,
    }


graphql_app = GraphQL(
    schema,
    context_value=get_context,
    http_handler=GraphQLHTTPHandler(extensions=[SQLAlchemyDataLoaderExtension]),
)


@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = Starlette(
    debug=True,
    lifespan=lifespan,
    middleware=[Middleware(DBSessionMiddleware)],
)
app.mount("/", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
