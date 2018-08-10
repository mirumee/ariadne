from typing import Any

from graphql import GraphQLSchema, graphql, parse


def execute_query(schema: GraphQLSchema, query: str, root_value: Any = None):
    query_ast = parse(query)
    return graphql(schema, query_ast, root_value)
