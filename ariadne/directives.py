import enum

from typing import Callable, List, Optional, cast

from graphql.type import GraphQLNamedType, GraphQLObjectType, GraphQLSchema

from .types import Resolver, SchemaBindable


class DirectiveType(SchemaBindable):
    _field: Resolver

    def __init__(self, name: str) -> None:
        self.name = name
        self._field = None

    def field(self, f: Resolver) -> Callable[[Resolver], Resolver]:
        self._field = f
        return f

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        directive = schema.get_directive(self.name)
        if not directive:
            raise ValueError("Directive %s is not defined in the schema" % self.name)

        for object_type in schema.type_map.values():
            if _type_implements_interface(self.name, object_type):
                self.bind_resolvers_to_graphql_type(object_type, replace_existing=False)

        for graphql_type in schema.type_map.values():
            if not isinstance(graphql_type, GraphQLObjectType):
                continue

            for field in graphql_type.fields.values():
                if field.ast_node:
                    for directive in field.ast_node.directives:
                        if directive.name.value != self.name:
                            continue

                        arguments = {}
                        for arg in directive.arguments:
                            arguments[arg.name.value] = arg.value.value
                        self._field(field, **arguments)
