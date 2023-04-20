from ariadne.asgi import GraphQL

from .schema import schema

app = GraphQL(schema, debug=True)
