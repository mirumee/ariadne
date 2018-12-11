from typing import List, Union

from .types import Bindable
from .wsgi_middleware import GraphQLMiddleware


def start_simple_server(
    type_defs: Union[str, List[str]],
    resolvers: Union[Bindable, List[Bindable], None] = None,
    host: str = "127.0.0.1",
    port: int = 8888,
) -> None:
    try:
        print("Simple GraphQL server is running on the http://%s:%s" % (host, port))
        graphql_server = GraphQLMiddleware.make_simple_server(
            type_defs, resolvers, host, port
        )
        graphql_server.serve_forever()
    except KeyboardInterrupt:
        pass
