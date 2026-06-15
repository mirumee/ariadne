"""
This is the simplest correct setup of the SQLAlchemy integration. Every root
field on the schema is auto-resolved by `SQLAlchemyQueryType`, so the only
thing the GraphQL context needs is a SQLAlchemy `session`.

Self-contained: a single file, an in-memory SQLite database, a synchronous
`Session`, and the schema/seed data inline. Run it and hit the endpoint with
queries like `{ posts { title author { username } } }` to see one optimised
SQL statement issued per top-level field.

Note on async: SQLAlchemy's `AsyncSession` *can* be plugged in by swapping
`create_engine`/`sessionmaker` for `create_async_engine`/`async_sessionmaker`,
but two sibling root resolvers awaiting the same `AsyncSession` race on its
single underlying connection and SQLAlchemy raises
`InvalidRequestError: This session is provisioning a new connection;
concurrent operations are not permitted`. The synchronous `Session` used
here executes sequentially by definition and is unaffected.

Run with:

    uv run \
        --with "uvicorn[standard]" \
        --with ariadne \
        --with "sqlalchemy" \
        --with "aiodataloader" \
        uvicorn examples.sqlalchemy.01_auto_eager_load:app --reload
"""

from contextlib import asynccontextmanager

from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.sqlalchemy import (
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
        session.add_all(
            [
                alice,
                bob,
                python_tag,
                graphql_tag,
                Post(
                    title="Hello, GraphQL",
                    author=alice,
                    tags=[python_tag, graphql_tag],
                ),
                Post(title="SQLAlchemy 2.0 tips", author=bob, tags=[graphql_tag]),
            ]
        )
        session.commit()


# --- GraphQL schema --------------------------------------------------------

type_defs = """
    type Query {
        users: [User!]!
        user(id: ID!): User

        posts: [Post!]!
        post(id: ID!): Post

        tags: [Tag!]!
        tag(id: ID!): Tag
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
query_type = SQLAlchemyQueryType([user_type, post_type, tag_type])

schema = make_executable_schema(type_defs, [query_type, user_type, post_type, tag_type])


async def get_context(request, _data):
    return {"request": request, "session": request.state.session}


graphql_app = GraphQL(
    schema,
    context_value=get_context,
    http_handler=GraphQLHTTPHandler(),
)


@asynccontextmanager
async def lifespan(_app):
    ## For testing purposes
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
