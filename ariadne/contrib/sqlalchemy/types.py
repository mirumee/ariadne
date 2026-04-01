from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from sqlalchemy.orm.strategy_options import _AbstractLoad


class LoadStrategy(Protocol):
    """
    SQLAlchemy relationship loading strategy functions (``joinedload``,
    ``selectinload``, ``subqueryload``, ``lazyload``, ``raiseload``, ``noload``,
    ``immediateload``, ``contains_eager``, ``defaultload``).
    """

    @property
    def __name__(self) -> str: ...

    def __call__(self, *args: Any, **kwargs: Any) -> _AbstractLoad: ...
