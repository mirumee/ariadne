from typing_extensions import TypeAliasType


class ForwardConnectionArguments:
    first: int | None
    after: str | None

    def __init__(self, *, first: int | None = None, after: str | None = None) -> None:
        self.first = first
        self.after = after


class BackwardConnectionArguments:
    last: int | None
    before: str | None

    def __init__(self, *, last: int | None = None, before: str | None = None) -> None:
        self.last = last
        self.before = before


class ConnectionArguments(ForwardConnectionArguments, BackwardConnectionArguments): ...


ConnectionArgumentsUnion = TypeAliasType(
    "ConnectionArgumentsUnion",
    ForwardConnectionArguments | BackwardConnectionArguments | ConnectionArguments,
)
ConnectionArgumentsTypeUnion = TypeAliasType(
    "ConnectionArgumentsTypeUnion",
    type[ForwardConnectionArguments]
    | type[BackwardConnectionArguments]
    | type[ConnectionArguments],
)
