from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from graphql import GraphQLObjectType, GraphQLSchema
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty, class_mapper

from ...objects import ObjectType
from .dataloaders import LoaderRegistry
from .types import LoadStrategy


class SQLAlchemyObjectType(ObjectType):
    """
    ObjectType specialized for SQLAlchemy models.
    Automatically binds resolvers for relationships using DataLoaders.
    """

    model: type[DeclarativeBase]
    aliases: dict[str, str]
    strategies: dict[str, LoadStrategy]
    max_depth: int
    _registry_key: str

    def __init__(
        self,
        name: str,
        model: type[DeclarativeBase],
        *,
        aliases: dict[str, str] | Callable[[], dict[str, str]] | None = None,
        strategies: dict[str, LoadStrategy] | None = None,
        max_depth: int = 3,
    ):
        super().__init__(name)
        self.model = model
        self.aliases = aliases() if callable(aliases) else (aliases or {})  # ty: ignore[call-top-callable]
        self.strategies = strategies or {}
        self.max_depth = max_depth

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        """Binds this `SQLAlchemyObjectType` to the GraphQL schema.

        Auto-generates resolvers for the model's relationships and aliased
        columns, then delegates to `ObjectType.bind_to_schema` to wire them
        (along with any explicitly-set resolvers) onto the schema's fields.

        The auto-resolvers must be registered before calling `super()` so
        they are included when the parent iterates `self._resolvers` to
        populate the GraphQL type's field `resolve` attributes.
        """
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)
        self._bind_auto_resolvers(cast(GraphQLObjectType, graphql_type))
        super().bind_to_schema(schema)

    def get_base_query(self, info: Any, **kwargs: Any):
        """
        Returns the base SQLAlchemy select statement for root queries.
        Can be overridden to apply default filters.
        """
        return select(self.model)

    def _bind_auto_resolvers(self, graphql_type: GraphQLObjectType) -> None:
        schema_fields = graphql_type.fields
        mapper = class_mapper(self.model)

        for gql_field, db_attr in self.aliases.items():
            if gql_field not in schema_fields:
                continue
            if callable(db_attr):
                self.set_field(gql_field, db_attr)
            else:
                self.set_field(
                    gql_field, lambda obj, *_, _attr=db_attr: getattr(obj, _attr)
                )

        for relation in mapper.relationships:
            if relation.key not in schema_fields:
                continue
            if relation.key in self._resolvers:
                continue
            self.set_field(relation.key, self._create_relation_resolver(relation))

    @staticmethod
    def get_loader_registry_from_context(context: Any) -> LoaderRegistry:
        """Get the `LoaderRegistry` from the GraphQL context.

        Override this method to customize how the registry is retrieved.
        """
        try:
            return context["loader_registry"]
        except KeyError:
            raise RuntimeError(
                "LoaderRegistry not found in context under key 'loader_registry'"
            )

    def _create_relation_resolver(self, relation: RelationshipProperty):
        async def resolve(obj: Any, info: Any, **kwargs: Any):
            # If the attribute is already loaded (e.g. via joinedload/selectinload),
            # return it
            if relation.key in obj.__dict__:
                return getattr(obj, relation.key)

            loader_registry = self.get_loader_registry_from_context(info.context)

            # Identify which column(s) on the current object connect it to the
            # target table. For a One-to-Many, this is usually a Foreign Key.
            local_relation_columns = [
                c.key for c in relation.local_columns if c.key is not None
            ]

            # Extract the actual database values from this specific object instance.
            join_values = tuple(getattr(obj, col) for col in local_relation_columns)

            # If it's a standard single-column relationship, unwrap the tuple to just
            # the ID. If it's a composite key, keep the tuple.
            lookup_key = join_values[0] if len(join_values) == 1 else join_values

            loader = loader_registry.get_loader(relation)
            return await loader.load(lookup_key)

        return resolve
