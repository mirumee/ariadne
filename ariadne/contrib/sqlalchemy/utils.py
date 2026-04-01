from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from graphql import GraphQLError
from sqlalchemy.orm import class_mapper, joinedload, load_only, selectinload

from .types import LoadStrategy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Mapper, RelationshipProperty
    from sqlalchemy.orm.strategy_options import _AbstractLoad

    from .objects import SQLAlchemyObjectType

logger = logging.getLogger(__name__)


def _resolve_load_option(
    mapper: Mapper[Any],
    db_attr: str,
    strategy: LoadStrategy | None,
    rel: RelationshipProperty[Any],
    load_path: _AbstractLoad | None,
) -> _AbstractLoad:
    """Resolve a SQLAlchemy loading strategy for a relationship attribute.

    Args:
        mapper: The SQLAlchemy mapper for the current model.
        db_attr: The database attribute name of the relationship.
        strategy: A SQLAlchemy loader function (e.g. ``selectinload``,
            ``joinedload``, ``subqueryload``). When ``None``, defaults to
            ``selectinload`` for collections and ``joinedload`` for scalars.
        rel: The SQLAlchemy relationship property being loaded.
        load_path: The parent loading chain to nest this option under.
            At the root level this is ``None`` and the strategy is called
            directly (e.g. ``selectinload(Post.tags)``). For nested
            relationships it is the ``_AbstractLoad`` returned by the
            parent strategy call, and the corresponding method is chained
            onto it (e.g. ``selectinload(Post.tags).selectinload(Tag.posts)``).

    Returns:
        A SQLAlchemy load option that can be passed to ``Query.options()``.
    """
    attr = getattr(mapper.class_, db_attr)
    if strategy is None:
        strategy = selectinload if rel.uselist else joinedload
    if load_path is not None:
        method_name: str = getattr(strategy, "__name__")
        return getattr(load_path, method_name)(attr)
    return strategy(attr)


def _build_options(
    mapper: Mapper[Any],
    selections: Sequence[Any],
    strategies: dict[str, LoadStrategy],
    aliases: dict[str, str],
    type_depths: dict[type[Any], int],
    load_path: _AbstractLoad | None = None,
    type_registry: dict[type[Any], SQLAlchemyObjectType] | None = None,
) -> list[_AbstractLoad]:
    current_type = mapper.class_
    current_depth = type_depths.get(current_type, 0)

    # Look up this type's config from registry
    type_config = type_registry.get(current_type) if type_registry else None
    max_depth = type_config.max_depth if type_config else 3

    if current_depth > max_depth:
        type_name = current_type.__name__
        raise GraphQLError(
            f"Query exceeds max_depth={max_depth} for type '{type_name}'. "
            f"Current depth: {current_depth}."
        )

    options = []

    # Process scalar fields using load_only
    scalar_fields = []
    for s in selections:
        gql_field = s.name.value
        db_attr = aliases.get(gql_field, gql_field)
        if (
            db_attr not in mapper.relationships
            and hasattr(mapper.class_, db_attr)
            and not callable(getattr(mapper.class_, db_attr))
        ):
            scalar_fields.append(db_attr)

    if scalar_fields:
        # Ensure local columns of all relationships (e.g., Foreign Keys)
        # are also loaded to prevent N+1 queries when falling back to DataLoaders.
        for rel in mapper.relationships.values():
            for col in rel.local_columns:
                if (
                    col.key is not None
                    and hasattr(mapper.class_, col.key)
                    and col.key not in scalar_fields
                ):
                    scalar_fields.append(col.key)

        class_attrs = [getattr(mapper.class_, s) for s in scalar_fields]
        if load_path is not None:
            options.append(load_path.load_only(*class_attrs))
        else:
            options.append(load_only(*class_attrs))

    # Process relationships
    for field_node in selections:
        gql_field = field_node.name.value
        db_attr = aliases.get(gql_field, gql_field)

        if db_attr in mapper.relationships:
            rel = mapper.relationships[db_attr]
            target_type = rel.mapper.class_

            # Look up child type's config
            child_config = type_registry.get(target_type) if type_registry else None
            child_strategies = child_config.strategies if child_config else strategies
            child_aliases = child_config.aliases if child_config else {}

            # Increment depth for target type
            new_type_depths = type_depths.copy()
            new_type_depths[target_type] = new_type_depths.get(target_type, 0) + 1

            strategy = strategies.get(gql_field)
            opt = _resolve_load_option(mapper, db_attr, strategy, rel, load_path)
            options.append(opt)

            if field_node.selection_set:
                nested_options = _build_options(
                    rel.mapper,
                    field_node.selection_set.selections,
                    child_strategies,
                    child_aliases,
                    new_type_depths,
                    load_path=opt,
                    type_registry=type_registry,
                )
                options.extend(nested_options)

    return options


def auto_eager_load(
    query: Any,
    info: Any,
    model: type[Any],
    strategies: dict[str, LoadStrategy] | None = None,
    aliases: dict[str, str] | None = None,
    max_depth: int = 3,
    type_registry: dict[type[Any], SQLAlchemyObjectType] | None = None,
) -> Any:
    """Automatically apply eager loading options based on the GraphQL selection set.

    Inspects the incoming GraphQL query and adds ``selectinload()``,
    ``joinedload()``, and ``load_only()`` (or any other SQLAlchemy loading
    strategy) for fields found in the selection set.

    Depth is tracked per-type: each type counts how many times it has been
    entered from the root. When a type's depth exceeds its ``max_depth``,
    a ``GraphQLError`` is raised.
    """
    resolved_strategies: dict[str, LoadStrategy] = strategies or {}
    resolved_aliases: dict[str, str] = aliases or {}
    mapper = class_mapper(model)
    selections = []

    for field_node in info.field_nodes:
        if field_node.selection_set:
            selections.extend(field_node.selection_set.selections)

    if not selections:
        return query

    type_depths = {model: 1}

    options = _build_options(
        mapper,
        selections,
        resolved_strategies,
        resolved_aliases,
        type_depths,
        type_registry=type_registry,
    )
    if options:
        query = query.options(*options)

    return query
