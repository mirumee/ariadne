from typing import List, Type

from graphql import GraphQLSchema


class BaseType:
    __abstract__ = True
    __schema__: str
    __requires__: List[Type["BaseType"]] = []

    graphql_name: str

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        raise NotImplementedError()
