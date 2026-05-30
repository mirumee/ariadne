from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, NamedTuple

from graphql import GraphQLError
from graphql.language import FieldNode, FragmentSpreadNode, InlineFragmentNode
from sqlalchemy.orm import class_mapper, joinedload, load_only, selectinload

from .types import LoadStrategy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.orm import Mapper, RelationshipProperty
    from sqlalchemy.orm.strategy_options import _AbstractLoad

    from .objects import SQLAlchemyObjectType

logger = logging.getLogger(__name__)


class DepthLimit(NamedTuple):
    max: int
    set_by: str


def _flatten_selections(
    selections: Sequence[Any],
    fragments: dict[str, Any] | None,
) -> list[FieldNode]:
    """Return only FieldNodes, expanding inline and named fragments recursively.

    Example — given ``{ ... on Post { title } ...PostFields }`` with
    ``PostFields`` defined as ``{ author { id } }``, returns
    ``[FieldNode("title"), FieldNode("author")]``.
    """
    result: list[FieldNode] = []
    for node in selections:
        if isinstance(node, FieldNode):
            result.append(node)
        elif isinstance(node, InlineFragmentNode) and node.selection_set:
            result.extend(_flatten_selections(node.selection_set.selections, fragments))
        elif isinstance(node, FragmentSpreadNode) and fragments:
            fragment = fragments.get(node.name.value)
            if fragment and fragment.selection_set:
                result.extend(
                    _flatten_selections(fragment.selection_set.selections, fragments)
                )
    return result


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
    depth_limit: DepthLimit,
    type_registry: dict[type[Any], SQLAlchemyObjectType],
    current_depth: int = 1,
    load_path: _AbstractLoad | None = None,
    fragments: dict[str, Any] | None = None,
) -> list[_AbstractLoad]:
    # Apply this type's max_depth if it is tighter than the inherited limit.
    current_config = type_registry.get(mapper.class_)
    if current_config and current_config.max_depth < depth_limit.max:
        depth_limit = DepthLimit(current_config.max_depth, mapper.class_.__name__)

    if current_depth > depth_limit.max:
        raise GraphQLError(
            f"Query depth {current_depth} exceeds max_depth={depth_limit.max}"
            f" (set by '{depth_limit.set_by}')."
        )

    options = []
    flat_selections = _flatten_selections(selections, fragments)

    # Process scalar fields using load_only
    scalar_fields = []
    for field_node in flat_selections:
        gql_field = field_node.name.value
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
    for field_node in flat_selections:
        gql_field = field_node.name.value
        db_attr = aliases.get(gql_field, gql_field)

        if db_attr in mapper.relationships:
            rel = mapper.relationships[db_attr]
            target_type = rel.mapper.class_

            child_config = type_registry.get(target_type)
            child_strategies = child_config.strategies if child_config else strategies
            child_aliases = child_config.aliases if child_config else {}

            strategy = strategies.get(gql_field)
            opt = _resolve_load_option(mapper, db_attr, strategy, rel, load_path)
            options.append(opt)

            if field_node.selection_set:
                nested_options = _build_options(
                    rel.mapper,
                    field_node.selection_set.selections,
                    child_strategies,
                    child_aliases,
                    depth_limit,
                    type_registry,
                    current_depth=current_depth + 1,
                    load_path=opt,
                    fragments=fragments,
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

    Each relationship level increments a depth counter. When it exceeds
    ``max_depth``, a ``GraphQLError`` is raised. Per-type ``max_depth`` values
    in ``type_registry`` can lower the limit further; the error names the type
    that set the tightest bound.
    """
    resolved_strategies: dict[str, LoadStrategy] = strategies or {}
    resolved_aliases: dict[str, str] = aliases or {}
    resolved_registry: dict[type[Any], SQLAlchemyObjectType] = type_registry or {}
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
        resolved_strategies,
        resolved_aliases,
        DepthLimit(max_depth, model.__name__),
        resolved_registry,
        fragments=getattr(info, "fragments", None),
    )
    if options:
        query = query.options(*options)

    return query
