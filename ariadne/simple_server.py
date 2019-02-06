from wsgiref import simple_server

from graphql import GraphQLSchema

from .wsgi import GraphQL


def start_simple_server(
    schema: GraphQLSchema,
    *,
    host: str = "127.0.0.1",
    port: int = 8888,
    server_class: type = GraphQL
) -> None:
    try:
        print("Simple GraphQL server is running on the http://%s:%s" % (host, port))
        wsgi_app = server_class(schema)
        graphql_server = simple_server.make_server(host, port, wsgi_app)
        graphql_server.serve_forever()
    except KeyboardInterrupt:
        pass
