from graphql import GraphQLSchema, graphql, parse


def execute_request(schema: GraphQLSchema, query: str, root_value: any=None):
    query_ast = parse(query)
    return graphql(schema, query_ast, root_value)