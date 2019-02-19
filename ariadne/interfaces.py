from graphql.type import GraphQLInterfaceType, GraphQLObjectType, GraphQLSchema

from .resolvers import ResolverMap


class Interface(ResolverMap):
    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        self.validate_graphql_type(graphql_type)

        for object_type in schema.type_map.values():
            if type_implements_interface(self.name, object_type):
                self.bind_resolvers_to_graphql_type(object_type, replace_existing=False)

    def validate_graphql_type(self, graphql_type: str) -> None:
        if not graphql_type:
            raise ValueError("Interface %s is not defined in the schema" % self.name)
        if not isinstance(graphql_type, GraphQLInterfaceType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (
                    self.name,
                    type(graphql_type).__name__,
                    GraphQLInterfaceType.__name__,
                )
            )


def type_implements_interface(interface: str, graphql_type: GraphQLObjectType) -> bool:
    if not isinstance(graphql_type, GraphQLObjectType):
        return False
    return interface in [i.name for i in graphql_type.interfaces]
