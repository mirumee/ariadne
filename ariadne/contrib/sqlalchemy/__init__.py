try:
    from .dataloaders import LoaderRegistry, SQLAlchemyRelationLoader
    from .objects import SQLAlchemyObjectType
    from .query import SQLAlchemyQueryType
    from .utils import auto_eager_load
except ImportError as ex:
    raise ImportError(
        "SQLAlchemy integration requires the 'sqlalchemy' and 'aiodataloader' "
        "packages. Install them using 'pip install \"ariadne[sqlalchemy]\"'."
    ) from ex

__all__ = [
    "LoaderRegistry",
    "SQLAlchemyObjectType",
    "SQLAlchemyQueryType",
    "SQLAlchemyRelationLoader",
    "auto_eager_load",
]
