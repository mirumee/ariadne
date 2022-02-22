from typing import Any, List, Optional

from graphql import ObjectTypeDefinitionNode

from .base_type import BaseType


class DeferredType(BaseType):
    __root__: Optional[Any]
    __requires__: List[BaseType] = []
    _graphql_name: str
    _graphql_type = ObjectTypeDefinitionNode

    def __init__(self, name: str, __root__: Optional[Any] = None):
        self._graphql_name = name
        self.__root__ = __root__
