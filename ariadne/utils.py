from graphql import parse
from typing import List, Union

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
