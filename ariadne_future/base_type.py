from typing import List

from graphql import GraphQLSchema


class BaseType:
    __schema__: str
    __requires__: List["BaseType"] = []

    def bind_to_schema(self, schema: GraphQLSchema):
        raise NotImplementedError()
