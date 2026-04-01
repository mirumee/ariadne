# SQLAlchemy Integration

Ariadne provides an optional integration for [SQLAlchemy 2.0](https://www.sqlalchemy.org/) that simplifies building GraphQL APIs on top of SQLAlchemy models.

This integration automates the creation of resolvers for database relationships using optimized [DataLoaders](https://github.com/graphql/dataloader) and provides utilities for "lookahead" eager loading.

## Installation

To use the SQLAlchemy integration, you need to install `ariadne` with the `sqlalchemy` extra:

```console
pip install ariadne[sqlalchemy]
```

This will also install `aiodataloader` and `aiosqlite` (if using SQLite).

## Core Features

### `SQLAlchemyObjectType`

`SQLAlchemyObjectType` is a specialized subclass of `ObjectType` that uses SQLAlchemy's ORM reflection to automatically generate resolvers for all relationships defined on a model.

- **Automatic N+1 Prevention**: It automatically uses DataLoaders for all relationship resolvers.
- **Support for M2M, M2O, and O2M**: Handles all standard SQLAlchemy relationship types out of the box.
- **Custom Aliases**: Map GraphQL field names to different SQLAlchemy attribute names.
- **Eager Loading Strategies**: Control how nested data is loaded (`joinedload` vs `selectinload`).
- **Max Depth Control**: Limit the depth of automatic lookahead optimization.
- **Column-level Optimization**: Automatically uses SQLAlchemy's `load_only` to fetch only the columns requested in the GraphQL query.

### `SQLAlchemyQueryType`

A custom `Query` type that automatically wires up root `Query` fields to their corresponding SQLAlchemy models by inspecting the GraphQL schema during its initialization, preventing redundant schema parsing.

### `auto_eager_load`

A "lookahead" optimization utility that parses the GraphQL selection set and automatically applies SQLAlchemy eager loading and column-level `load_only` to a query, bypassing DataLoaders for top-level relationships for better performance.

## Example Usage

Here is a complete example demonstrating how to use the SQLAlchemy integration with different relationship types and optimizations.

```python
from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.contrib.sqlalchemy import (
    LoaderRegistry,
    SQLAlchemyObjectType,
    SQLAlchemyQueryType,
)
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, selectinload

# Define SQLAlchemy models
Base = declarative_base()

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.post_id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    post_id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    posts = relationship("Post", secondary=post_tags, back_populates="tags")

# Define GraphQL schema
type_defs = """
    type Query {
        posts: [Post!]!
        users: [User!]!
        post(id: ID!): Post
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

# Register SQLAlchemyObjectType for models
# Use 'aliases' to map GraphQL 'id' to SQLAlchemy 'post_id'
# Use 'strategies' to specify eager loading for relationships
# Use 'max_depth' to limit lookahead optimization depth
post_type = SQLAlchemyObjectType(
    "Post", 
    Post, 
    aliases={"id": "post_id"},
    strategies={"tags": selectinload, "author": selectinload},
    max_depth=2
)
user_type = SQLAlchemyObjectType("User", User)
tag_type = SQLAlchemyObjectType("Tag", Tag)

# Automatically bind root queries
query = SQLAlchemyQueryType("Query", [post_type, user_type, tag_type])

schema = make_executable_schema(type_defs, [query, post_type, user_type, tag_type])


# Context value must provide 'session' and 'loader_registry'
async def get_context_value(request, data):
    async with AsyncSessionLocal() as session:
        return {
            "session": session,
            "loader_registry": LoaderRegistry(session),
        }

app = GraphQL(schema, context_value=get_context_value)
```

## Advanced Customization

### Custom Base Query

You can subclass `SQLAlchemyObjectType` and override `get_base_query` to apply default filters, such as row-level security or soft-delete filtering.

```python
class MyPostsType(SQLAlchemyObjectType):
    def get_base_query(self, info, **kwargs):
        current_user = info.context.get("current_user")
        return select(self.model).where(self.model.author_id == current_user.id)

post_type = MyPostsType("Post", Post)
```

### Manual Resolver Overrides

Since `SQLAlchemyObjectType` is an `ObjectType`, you can still use the `@field` decorator to provide custom logic for specific fields. Your manual resolver will take precedence over the auto-generated one.

```python
@post_type.field("summary")
def resolve_post_summary(obj, *_):
    return obj.title[:20] + "..."
```

## Performance Considerations

### Automatic Lookahead
By default, `SQLAlchemyQueryType` uses `auto_eager_load` to pre-fetch relationships requested in the GraphQL query up to `max_depth`. This is highly efficient and prevents N+1 problems for the most common use cases. 

### Column-Level Optimization
The integration automatically detects which scalar fields are requested in the GraphQL query and uses SQLAlchemy's `load_only()` to avoid fetching large blobs or unnecessary columns from the database.

### DataLoaders Fallback
For nests deeper than `max_depth`, the system falls back to DataLoaders (`SQLAlchemyRelationLoader`), which still prevents N+1 by batching requests but might result in more database roundtrips than a single complex join.
