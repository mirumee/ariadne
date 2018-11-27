from typing import List, Union

from graphql import parse

from .wsgi_middleware import GraphQLMiddleware


def gql(value: str) -> str:
    parse(value)
    return value


def start_simple_server(
    type_defs: Union[str, List[str]],
    resolvers: Union[dict, List[dict]],
    host: str = "127.0.0.1",
    port: int = 8888,
):
    try:
        print("Simple GraphQL server is running on the http://%s:%s" % (host, port))
        graphql_server = GraphQLMiddleware.make_simple_server(
            type_defs, resolvers, host, port
        )
        graphql_server.serve_forever()
    except KeyboardInterrupt:
        pass


def convert_graphql_name_to_python_name(graphql_name):
    python_name = ""
    for i, c in enumerate(graphql_name.lower()):
        if c != graphql_name[i]:
            python_name += "_"
        python_name += c
    return python_name