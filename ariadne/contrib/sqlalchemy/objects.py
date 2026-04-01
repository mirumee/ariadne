from collections.abc import Callable
from typing import Any

from graphql import GraphQLSchema
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty, class_mapper

from ...objects import ObjectType
from .dataloaders import LoaderRegistry, SQLAlchemyRelationLoader


class SQLAlchemyObjectType(ObjectType):
    """
    ObjectType specialized for SQLAlchemy models.
    Automatically binds resolvers for relationships using DataLoaders.
    """

    model: type[DeclarativeBase]
    aliases: Any
    strategies: dict[str, Any]
    max_depth: int
    loader_registry_key: str

    def __init__(
        self,
        name: str,
        model: type[DeclarativeBase],
        *,
        aliases: dict[str, str] | Callable[[], dict[str, str]] | None = None,
        strategies: dict[str, Any] | None = None,
        max_depth: int = 3,
        loader_registry_key: str = "loader_registry",
    ):
        super().__init__(name)
        self.model = model
        self.aliases = aliases or {}
        self.strategies = strategies or {}
        self.max_depth = max_depth
        self.loader_registry_key = loader_registry_key

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        self._bind_auto_resolvers()
        super().bind_to_schema(schema)

    def get_base_query(self, info: Any, **kwargs: Any):
        """
        Returns the base SQLAlchemy select statement for root queries.
        Can be overridden to apply default filters.
        """
        return select(self.model)

    def _bind_auto_resolvers(self):
        mapper = class_mapper(self.model)

        if callable(self.aliases):
            self.aliases = self.aliases()

        # Bind field aliases
        for gql_field, db_attr in self.aliases.items():
            if callable(db_attr):
                self.set_field(gql_field, db_attr)
            else:
                self.set_field(
                    gql_field, lambda obj, *_, _attr=db_attr: getattr(obj, _attr)
                )

        # Bind relationships
        for relation in mapper.relationships:
            if relation.key not in self._resolvers:
                self.set_field(relation.key, self._create_relation_resolver(relation))

    def _create_relation_resolver(self, relation: RelationshipProperty):
        async def resolve(obj: Any, info: Any, **kwargs: Any):
            # If the attribute is already loaded (e.g. via joinedload/selectinload),
            # return it
            if relation.key in obj.__dict__:
                return getattr(obj, relation.key)

            registry: LoaderRegistry = info.context.get(self.loader_registry_key)
            if registry is None:
                raise RuntimeError(
                    "LoaderRegistry not found in context under key "
                    f"'{self.loader_registry_key}'"
                )

            # Build the key for the loader
            local_cols = [c.key for c in relation.local_columns]
            key = tuple(getattr(obj, k) for k in local_cols)  # ty: ignore[invalid-argument-type]
            if len(key) == 1:
                key = key[0]

            loader = registry.get_loader(relation, SQLAlchemyRelationLoader)
            return await loader.load(key)

        return resolve
