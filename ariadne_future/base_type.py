from typing import List, Type

from graphql import GraphQLSchema


class BaseType:
    __schema__: str

    graphql_name: str

    __abstract__ = True
    __requires__: List[Type["BaseType"]] = []

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        raise NotImplementedError()
