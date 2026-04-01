import logging
from collections import defaultdict
from typing import Any

from aiodataloader import DataLoader
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import RelationshipProperty

logger = logging.getLogger(__name__)


class SQLAlchemyRelationLoader(DataLoader):
    """
    DataLoader for SQLAlchemy relationships supporting:
    - Composite Keys
    - Many-to-Many (secondary tables)
    - Result grouping via SQL columns (optimized)
    """

    def __init__(
        self,
        session: AsyncSession,
        relation_prop: RelationshipProperty,
        cache: bool = True,
    ):
        super().__init__(cache=cache)
        self.session = session
        self.relation_prop = relation_prop
        self.target_model = relation_prop.mapper.class_
        self.is_list = relation_prop.uselist

        # Identify local and remote columns (handles composite keys)
        if relation_prop.secondary is not None:
            self.local_cols = [lp.key for lp, rp in relation_prop.synchronize_pairs]
            self.remote_cols = [rp.key for lp, rp in relation_prop.synchronize_pairs]
        else:
            self.local_cols = [c.key for c in relation_prop.local_columns]
            self.remote_cols = [c.key for c in relation_prop.remote_side]

        self.secondary = relation_prop.secondary

    def get_query(self, keys: list[Any]):
        """Builds query. Handles composite IN clause and M2M joins."""
        target_model = self.target_model
        stmt = select(target_model)

        if self.secondary is not None:
            stmt = stmt.join(self.secondary)
            filter_cols = [self.secondary.c[k] for k in self.remote_cols]  # ty: ignore[invalid-argument-type]
        else:
            filter_cols = [getattr(target_model, k) for k in self.remote_cols]  # ty: ignore[invalid-argument-type]

        # Add the filtering columns to the result to allow grouping
        stmt = stmt.add_columns(*filter_cols)

        if len(filter_cols) > 1:
            stmt = stmt.where(tuple_(*filter_cols).in_(keys))
        else:
            # Flatten keys if they are single-element tuples
            flat_keys = [k[0] if isinstance(k, (list, tuple)) else k for k in keys]
            stmt = stmt.where(filter_cols[0].in_(flat_keys))

        return stmt

    async def batch_load_fn(self, keys: list[Any]) -> list[Any]:
        logger.debug(
            "SQLAlchemyRelationLoader: Fetching %s for %d parents",
            self.target_model.__name__,
            len(keys),
        )
        stmt = self.get_query(keys)
        result = await self.session.execute(stmt)
        rows = result.all()

        num_filter_cols = len(self.remote_cols)
        grouped = defaultdict(list)

        for row in rows:
            item = row[0]
            # The filter columns are appended after the model instance
            key_parts = row[1 : 1 + num_filter_cols]
            key = tuple(key_parts) if num_filter_cols > 1 else key_parts[0]
            grouped[key].append(item)

        return [
            grouped[k] if self.is_list else (grouped[k][0] if grouped[k] else None)
            for k in keys
        ]


class LoaderRegistry:
    """
    Keeps one DataLoader instance per relationship per request.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._loaders: dict[
            tuple[RelationshipProperty, type[DataLoader]], DataLoader
        ] = {}

    def get_loader(
        self,
        relation_prop: RelationshipProperty,
        loader_class: type[SQLAlchemyRelationLoader] = SQLAlchemyRelationLoader,
    ) -> DataLoader:
        key = (relation_prop, loader_class)
        if key not in self._loaders:
            self._loaders[key] = loader_class(self.session, relation_prop)
        return self._loaders[key]
