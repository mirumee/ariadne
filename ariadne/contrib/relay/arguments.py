from typing import Optional, Union

from typing_extensions import TypeAliasType


class ForwardConnectionArguments:
    first: Optional[int]
    after: Optional[str]

    def __init__(
        self, *, first: Optional[int] = None, after: Optional[str] = None
    ) -> None:
        self.first = first
        self.after = after


class BackwardConnectionArguments:
    last: Optional[int]
    before: Optional[str]

    def __init__(
        self, *, last: Optional[int] = None, before: Optional[str] = None
    ) -> None:
        self.last = last
        self.before = before


class ConnectionArguments:
    def __init__(
        self,
        *,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> None:
        self.first = first
        self.after = after
        self.last = last
        self.before = before


ConnectionArgumentsUnion = TypeAliasType(
    "ConnectionArgumentsUnion",
    Union[ForwardConnectionArguments, BackwardConnectionArguments, ConnectionArguments],
)
ConnectionArgumentsTypeUnion = TypeAliasType(
    "ConnectionArgumentsTypeUnion",
    Union[
        type[ForwardConnectionArguments],
        type[BackwardConnectionArguments],
        type[ConnectionArguments],
    ],
)
