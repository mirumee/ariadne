import logging
from typing import Any

from sqlalchemy.orm import class_mapper, joinedload, load_only, selectinload

logger = logging.getLogger(__name__)


def _resolve_load_option(mapper, db_attr, strategy, rel, load_path):
    attr = getattr(mapper.class_, db_attr)
    if strategy is joinedload:
        return load_path.joinedload(attr) if load_path else joinedload(attr)
    if rel.uselist:
        return load_path.selectinload(attr) if load_path else selectinload(attr)
    return load_path.joinedload(attr) if load_path else joinedload(attr)


def _build_options(
    mapper, selections, strategies, aliases, depth, max_depth, load_path=None
):
    if depth > max_depth:
        return []

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
                if hasattr(mapper.class_, col.key) and col.key not in scalar_fields:
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
            strategy = strategies.get(gql_field)
            opt = _resolve_load_option(mapper, db_attr, strategy, rel, load_path)

            options.append(opt)

            if field_node.selection_set:
                nested_options = _build_options(
                    rel.mapper,
                    field_node.selection_set.selections,
                    strategies,
                    {},  # Nested aliases not supported (model-specific)
                    depth + 1,
                    max_depth,
                    load_path=opt,
                )
                options.extend(nested_options)

    return options


def auto_eager_load(
    query: Any,
    info: Any,
    model: type[Any],
    strategies: dict[str, Any] | None = None,
    aliases: dict[str, Any] | None = None,
    max_depth: int = 3,
):
    """
    Lookahead Optimization:
    Automatically adds selectinload(), joinedload(), and load_only()
    for fields found in the GraphQL selection set up to `max_depth`.
    """
    strategies = strategies or {}
    aliases = aliases or {}
    mapper = class_mapper(model)
    selections = []

    for field_node in info.field_nodes:
        if field_node.selection_set:
            selections.extend(field_node.selection_set.selections)

    if not selections:
        return query

    options = _build_options(
        mapper,
        selections,
        strategies,
        aliases,
        depth=1,
        max_depth=max_depth,
    )
    if options:
        query = query.options(*options)

    return query
