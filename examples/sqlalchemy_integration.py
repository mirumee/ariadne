"""
Example: SQLAlchemy integration demonstrating relationships, eager loading,
and selective column loading.

Run with:

    uvicorn examples.sqlalchemy_integration:app --reload

or:
    uv run \
    --with "uvicorn[standard]" \
    --with ariadne \
    --with "sqlalchemy[asyncio]" \
    --with "aiodataloader" \
    --with "aiosqlite" \
    uvicorn examples.sqlalchemy_integration:app --reload

Sample Queries to test features:

1. One-to-Many & Callable Aliases
   (Observe the uppercase username due to the callable alias)
   query {
     users {
       id
       username
       posts {
         title
       }
     }
   }

2. Many-to-One & Column Optimization
   (Check server console: 'content' column is NOT queried because it's not requested)
   query {
     posts {
       title
       author {
         username
       }
     }
   }

3. Many-to-Many
   query {
     tags {
       name
       posts {
         title
       }
     }
   }

4. Max Depth Limit (Configured to 2 on Post)
   (Check server console: The first two levels use JOINs/subqueries.
   Deeper levels will trigger DataLoader fallback queries)
   query {
     posts {
       title
       author {          # Level 1 (Optimized)
         posts {         # Level 2 (Optimized)
           title
           tags {        # Level 3 (Exceeds max_depth=2, uses DataLoader)
             name
           }
         }
       }
     }
   }
"""

from contextlib import asynccontextmanager

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship, selectinload
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.contrib.sqlalchemy import (
    LoaderRegistry,
    SQLAlchemyObjectType,
    SQLAlchemyQueryType,
)

# --- Database Setup ---

Base = declarative_base()

# Many-to-Many Association Table
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.post_id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    posts = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"
    post_id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)  # New field to test selective loading
    is_published = Column(Boolean, default=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    posts = relationship("Post", secondary=post_tags, back_populates="tags")


# Enable echo=True to see the SQL queries in the console
# This allows verifying 'load_only' (only requested fields are fetched)
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        u1 = User(username="alice")
        u2 = User(username="bob")
        t1, t2 = Tag(name="Python"), Tag(name="GraphQL")
        p1 = Post(
            title="Published Post",
            content="Some long content...",
            tags=[t1, t2],
            is_published=True,
            author=u1,
        )
        p2 = Post(
            title="Draft Post",
            content="Draft content...",
            tags=[t1],
            is_published=False,
            author=u2,
        )
        session.add_all([u1, u2, t1, t2, p1, p2])
        await session.commit()


# --- GraphQL Schema ---

type_defs = """
    type Query {
        users: [User!]!
        user(id: ID!): User
        
        posts: [Post!]!
        post(my_post_id: ID!): Post
        publishedPosts: [Post!]!
        
        tags: [Tag!]!
        tag(id: ID!): Tag
    }

    type User {
        id: ID!
        username: String!
        posts: [Post!]!
    }

    type Post {
        my_post_id: ID!
        title: String!
        content: String!
        is_published: Boolean!
        author: User!
        tags: [Tag!]!
    }

    type Tag {
        id: ID!
        name: String!
        posts: [Post!]!
    }
"""

# --- SQLAlchemyObjectType Registrations ---

# User model (One-to-Many with Post)
user_type = SQLAlchemyObjectType(
    "User",
    User,
)

# Post model (Many-to-One with User, Many-to-Many with Tag)
# 'max_depth' controls how deep 'auto_eager_load' will go.
# If a query exceeds this depth, it falls back to DataLoaders.
# 'aliases' maps GQL field names to SQLAlchemy attribute names.
post_type = SQLAlchemyObjectType(
    "Post",
    Post,
    aliases=lambda: {"my_post_id": "post_id"},  # {"my_post_id": "post_id"}
    strategies={"tags": selectinload, "author": selectinload},
    max_depth=2,
)

# Tag model (Many-to-Many with Post)
tag_type = SQLAlchemyObjectType("Tag", Tag)

# Automatically bind Query fields (users, user, posts, tags, post, tag)
query = SQLAlchemyQueryType("Query", [user_type, post_type, tag_type])


# Custom query resolver for publishedPosts (demonstrating manual override)
@query.field("publishedPosts")
async def resolve_published_posts(_, info):
    session = info.context["session"]
    stmt = select(Post).where(Post.is_published)
    result = await session.execute(stmt)
    return result.scalars().unique().all()


schema = make_executable_schema(type_defs, [query, user_type, post_type, tag_type])


async def get_context_value(request, data):
    # It's important to create a new session and LoaderRegistry per request
    async with AsyncSessionLocal() as session:
        return {
            "session": session,
            "loader_registry": LoaderRegistry(session),
        }


graphql_app = GraphQL(schema, context_value=get_context_value)


@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield


app = Starlette(debug=True, lifespan=lifespan)
app.mount("/", graphql_app)


if __name__ == "__main__":
    # Example usage:
    # Run this script and use a GraphQL client to query the API.
    # Check the console output to see optimized SQL queries.
    # Note: Requires 'uvicorn', 'starlette' and 'aiosqlite' to be installed.
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
