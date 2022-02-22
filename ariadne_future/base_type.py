from typing import List

from graphql import GraphQLSchema


class BaseType:
    __schema__: str
    __requires__: List["BaseType"] = []

    _graphql_name: str

    def __bind_to_schema__(self, schema: GraphQLSchema):
        raise NotImplementedError()
