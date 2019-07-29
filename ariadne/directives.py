from typing import Type

from graphql.type import GraphQLSchema

from .types import SchemaBindable
from .schema_visitor import SchemaDirectiveVisitor


class DirectiveType(SchemaBindable):
    def __init__(self, name: str, visitor: Type[SchemaDirectiveVisitor]) -> None:
        self.name = name
        self.visitor = visitor

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        SchemaDirectiveVisitor.visit_schema_directives(
            schema, {self.name: self.visitor}
        )
