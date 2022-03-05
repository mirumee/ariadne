from graphql import ObjectTypeDefinitionNode

from .base_type import BaseType


class DeferredType(BaseType):
    graphql_type = ObjectTypeDefinitionNode

    def __init__(self, name: str):
        self.graphql_name = name

    @classmethod
    def __bind_to_schema__(cls, *_):
        raise NotImplementedError("DeferredType cannot be bound to schema")
