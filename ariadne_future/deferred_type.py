from typing import Any, Optional


class DeferredType:
    __root__: Optional[Any]
    __requires__ = []
    _graphql_name: str

    def __init__(self, name: str, __root__: Optional[Any] = None):
        self._graphql_name = name
        self.__root__ = __root__
