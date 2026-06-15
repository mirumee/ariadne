try:
    from .dataloaders import LoaderRegistry, SQLAlchemyDataLoader
    from .extension import SQLAlchemyDataLoaderExtension
    from .objects import SQLAlchemyObjectType
    from .query import SQLAlchemyQueryType
    from .types import LoadStrategy
    from .utils import auto_eager_load
except ImportError as ex:
    raise ImportError(
        "SQLAlchemy integration requires the 'sqlalchemy' and 'aiodataloader' "
        "packages. Install them using 'pip install \"ariadne[sqlalchemy]\"'."
    ) from ex

__all__ = [
    "SQLAlchemyDataLoaderExtension",
    "LoadStrategy",
    "LoaderRegistry",
    "SQLAlchemyObjectType",
    "SQLAlchemyQueryType",
    "SQLAlchemyDataLoader",
    "auto_eager_load",
]
