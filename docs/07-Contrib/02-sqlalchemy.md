---
id: sqlalchemy
title: SQLAlchemy Integration
sidebar_label: SQLAlchemy
---

Ariadne provides an optional integration for [SQLAlchemy 2.0](https://www.sqlalchemy.org/) that simplifies building GraphQL APIs on top of SQLAlchemy models.

The integration has two execution paths that work together:

1. **The `auto_eager_load` path** - `SQLAlchemyQueryType` builds *one* optimised SQL statement per top-level field by walking the GraphQL selection set ahead of time and applying `selectinload` / `joinedload` / `load_only` to whatever the client asked for. Most queries against an auto-resolved schema are fully served by this path.
2. **The DataLoader fallback path** - when a relationship is reached on a parent object that was *not* prepared by `auto_eager_load` (e.g. an object returned by a manual `@field` resolver), `SQLAlchemyObjectType` falls back to a `SQLAlchemyDataLoader` that batches the loads and prevents N+1.

This document is organised around those two paths, both of which are covered here end-to-end.

## Installation

Install `ariadne` with the `sqlalchemy` extra:

```console
pip install ariadne[sqlalchemy]
```

This installs `sqlalchemy` and `aiodataloader`.


> **Note:** The examples in this guide focus on the Ariadne integration and omit the infrastructure for database session management (such as middleware or extensions for automatic session creation and teardown). In production, you should use a framework-specific middleware or an Ariadne `Extension` to ensure sessions are correctly scoped to the request and closed after execution.


## Quick Start

The minimal correct setup uses a synchronous `Session` and puts it in the GraphQL context.

```python
from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sqlalchemy import (
    SQLAlchemyObjectType,
    SQLAlchemyQueryType,
)
from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

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
    username = Column(String)
    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    posts = relationship("Post", secondary=post_tags, back_populates="tags")


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

user_type = SQLAlchemyObjectType("User", User)
post_type = SQLAlchemyObjectType("Post", Post)
tag_type = SQLAlchemyObjectType("Tag", Tag)
query = SQLAlchemyQueryType([user_type, post_type, tag_type])

schema = make_executable_schema(type_defs, [query, user_type, post_type, tag_type])

engine = create_engine("sqlite:///db.sqlite3")
SessionLocal = sessionmaker(engine, expire_on_commit=False)


async def get_context(request, _data):
    return {"request": request, "session": SessionLocal()}


app = GraphQL(
    schema,
    context_value=get_context,
    http_handler=GraphQLHTTPHandler(),
)
```

`SQLAlchemyQueryType` reads the session from `info.context["session"]` and feeds it through the `auto_eager_load` path described below. Ariadne's `context_value` callable must return the context dict (or an awaitable that resolves to one) - async generator / `yield`-based forms are not supported, so deterministic per-request session cleanup is best handled via a custom `Extension` (the same mechanism `SQLAlchemyDataLoaderExtension` uses). Without one, the session is closed when its connection is returned to the pool by GC.

A complete runnable version of this Quick Start (in-memory SQLite, seed data, sample queries) lives in [`examples/sqlalchemy/01_auto_eager_load.py`](https://github.com/mirumee/ariadne/tree/main/examples/sqlalchemy/01_auto_eager_load.py).

### Reading the session from somewhere other than `context["session"]`

A common production pattern is to open the SQLAlchemy session in middleware (so the same scope handles both the GraphQL request and any other endpoints), attach it to `request.state.session`, and let resolvers read from there. `SQLAlchemyQueryType` looks the session up via `get_session_from_context`, which is a static method you can override on a subclass. Use that subclass everywhere you would have used `SQLAlchemyQueryType`:

```python

class MyType(SQLAlchemyQueryType):
    @staticmethod
    def get_session_from_context(context):
        return context["request"].state.session

query = MyType([user_type, post_type])
```

### Tuning per-type behaviour: `aliases`, `strategies`, `max_depth`

`SQLAlchemyObjectType` accepts three keyword-only arguments that change how its instance behaves on the `auto_eager_load` path:

- **`aliases`** — map a GraphQL field name to a different SQLAlchemy attribute. Honoured by both relationship resolution and the `load_only` column optimisation. Pass a dict, or a zero-arg callable returning a dict for lazy initialisation.
- **`strategies`** — override the default loader strategy (`selectinload` for collections, `joinedload` for scalars) on a per-relationship basis. Any SQLAlchemy loader function works — `selectinload`, `joinedload`, `subqueryload`, etc.
- **`max_depth`** — cap how deep `auto_eager_load` walks into this type from the root. Tracked **per-type**: each entry into the same type counts. Exceeding it raises `GraphQLError`. Defaults to `3`.

Minimal example covering all three:

```python
from sqlalchemy.orm import selectinload

post_type = SQLAlchemyObjectType(
    "Post",
    Post,
    aliases={"my_post_id": "post_id"},
    strategies={"author": selectinload, "tags": selectinload},
    max_depth=4,
)

query = SQLAlchemyQueryType([user_type, post_type])
```


-----
Custom resolvers and DataLoaders
-----

### Required setup for DataLoaders

For the DataLoader path to work, `loader_registry` must be present in `info.context`. The recommended way to put it there is the `SQLAlchemyDataLoaderExtension` — the bare class is a zero-arg callable, so you can pass it directly to the HTTP handler:

```python
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sqlalchemy import SQLAlchemyDataLoaderExtension

app = GraphQL(
    schema,
    context_value=get_context,  # only puts "session" in context now
    http_handler=GraphQLHTTPHandler(extensions=[SQLAlchemyDataLoaderExtension]),
)
```

With the extension enabled, your `get_context` only needs to put a `session` in the context — the extension creates a fresh `LoaderRegistry` per request before any resolver runs and writes it to `context["loader_registry"]`.

To use different keys or a custom `LoaderRegistry` subclass pass proper arguments to the extension:

```python
extensions=[
    SQLAlchemyDataLoaderExtension(
        session_key="db",
        registry_key="loaders",
    ),
]
```

If you'd rather wire the registry in `get_context` yourself, that still works — the extension's only job is to do this for you:

```python
from ariadne.contrib.sqlalchemy import LoaderRegistry


async def get_context(request, _data):
    session = request.state.session
    return {
        "request": request,
        "session": session,
        "loader_registry": LoaderRegistry(session),
    }
```


The `auto_eager_load` path only fires for fields that go through `SQLAlchemyQueryType`'s auto-resolver. The moment you write a manual `@field` resolver that runs its own `select(...)` and returns ORM objects, those rows bypass `auto_eager_load` entirely — their relationships are not pre-loaded, and resolving `author`/`tags`/etc. on them falls through to a per-request DataLoader. The DataLoader collects every per-row lookup for one relationship into a single batched SQL statement, so N+1 is avoided here too — by batching rather than by lookahead.

```python
@query.field("publishedPosts")
def resolve_published_posts(_, info):
    session = info.context["session"]
    stmt = select(Post).where(Post.is_published)
    return session.execute(stmt).scalars().unique().all()
```

For the GraphQL query:

```graphql
{
  publishedPosts {
    title
    author { username }
    tags { name }
  }
}
```

…the integration runs three SQL statements: the manual `WHERE is_published` query, then one batched `WHERE id IN (...)` for `author`, then one joined query through `post_tags` for `tags`.

A runnable version of this scenario lives at [`examples/sqlalchemy/02_dataloader_fallback.py`](https://github.com/mirumee/ariadne/tree/main/examples/sqlalchemy/02_dataloader_fallback.py). Run it with `echo=True` and watch the SQL log to confirm the three-statement count.



The registry **must** be created per request — sharing it across requests would leak DataLoader caches (and therefore data) between users. The simplest correct lifetime is "scoped to the same `Session` you put in the context".

To customise the lookup, override `SQLAlchemyObjectType.get_loader_registry_from_context` on a subclass - the same pattern as `get_session_from_context`:

```python
class MyObjectType(SQLAlchemyObjectType):
    @staticmethod
    def get_loader_registry_from_context(context):
        return context["request"].state.loaders
```

