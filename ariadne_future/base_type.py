from typing import List, Type

from graphql import DefinitionNode, GraphQLSchema

from .dependencies import Dependencies
from .types import RequirementsDict


class BaseType:
    __abstract__ = True
    __schema__: str
    __requires__: List[Type["BaseType"]] = []

    graphql_name: str
    graphql_type: Type[DefinitionNode]

    @classmethod
    def __get_requirements__(cls) -> RequirementsDict:
        return {req.graphql_name: req.graphql_type for req in cls.__requires__}

    @classmethod
    def __validate_requirements__(
        cls, requirements: RequirementsDict, dependencies: Dependencies
    ):
        for graphql_name in dependencies:
            if graphql_name not in requirements:
                raise ValueError(
                    f"{cls.__name__} class was defined without required GraphQL "
                    f"definition for '{graphql_name}' in __requires__"
                )

    @classmethod
    def __bind_to_schema__(cls, schema: GraphQLSchema):
        raise NotImplementedError()
