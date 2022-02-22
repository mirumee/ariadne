from typing import Any, List, Optional, Type

from graphql import ObjectTypeDefinitionNode

from .base_type import BaseType


class DeferredType(BaseType):
    __root__: Optional[Any]
    __requires__: List[Type[BaseType]] = []

    graphql_name: str
    graphql_type = ObjectTypeDefinitionNode

    def __init__(self, name: str, __root__: Optional[Any] = None):
        self.graphql_name = name
        self.__root__ = __root__

    @classmethod
    def __bind_to_schema__(cls, *_):
        raise NotImplementedError("DeferredType cannot be bound to schema")
