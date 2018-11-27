from .schema import Schema
from .wsgi_middleware import GraphQLMiddleware


def start_simple_server(schema: Schema, host: str = "127.0.0.1", port: int = 8888):
    try:
        print("Simple GraphQL server is running on the http://%s:%s" % (host, port))
        graphql_server = GraphQLMiddleware.make_simple_server(schema, host, port)
        graphql_server.serve_forever()
    except KeyboardInterrupt:
        pass
