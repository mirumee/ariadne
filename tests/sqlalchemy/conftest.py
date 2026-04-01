import pytest
from sqlalchemy import (
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import declarative_base, relationship


@pytest.fixture
def models():
    """ORM-only definitions mirroring examples/sqlalchemy/01_auto_eager_load.py.

    No engine, no DB - the tests mock `session.execute(...)` directly. Models
    only need to expose introspectable RelationshipProperty objects.
    """
    base = declarative_base()

    post_tags = Table(
        "post_tags",
        base.metadata,
        Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
        Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    )

    class User(base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        posts = relationship("Post", back_populates="author")

    class Post(base):
        __tablename__ = "posts"
        id = Column(Integer, primary_key=True)
        title = Column(String)
        author_id = Column(Integer, ForeignKey("users.id"))
        author = relationship("User", back_populates="posts")
        tags = relationship("Tag", secondary=post_tags, back_populates="posts")

    class Tag(base):
        __tablename__ = "tags"
        id = Column(Integer, primary_key=True)
        name = Column(String)
        posts = relationship("Post", secondary=post_tags, back_populates="tags")

    return {"User": User, "Post": Post, "Tag": Tag, "post_tags": post_tags}


@pytest.fixture
def composite_key_models():
    """Composite-PK/FK models for testing the `tuple_(...).in_(...)` branch."""
    base = declarative_base()

    class Region(base):
        __tablename__ = "regions"
        country = Column(String, primary_key=True)
        code = Column(String, primary_key=True)
        name = Column(String)
        cities = relationship("City", back_populates="region")

    class City(base):
        __tablename__ = "cities"
        id = Column(Integer, primary_key=True)
        name = Column(String)
        country = Column(String)
        region_code = Column(String)
        region = relationship("Region", back_populates="cities")

        __table_args__ = (
            ForeignKeyConstraint(
                ["country", "region_code"], ["regions.country", "regions.code"]
            ),
        )

    return {"Region": Region, "City": City}
