from typing import Any

from graphql import GraphQLResolveInfo

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL as GraphQLASGI
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.wsgi import GraphQL as GraphQLWSGI

schema = make_executable_schema(
    """
    type Query {
        hello: String
    }
    """
)


def example_middleware(next_, obj: Any, info: GraphQLResolveInfo, **kwargs: Any):
    return next_(obj, info, **kwargs)


def get_middlewares(request, context):
    return [example_middleware]


GraphQLASGI(
    schema,
    http_handler=GraphQLHTTPHandler(
        middleware=[example_middleware],
    ),
)

GraphQLASGI(
    schema,
    http_handler=GraphQLHTTPHandler(
        middleware=get_middlewares,
    ),
)

GraphQLWSGI(
    schema,
    middleware=[example_middleware],
)

GraphQLWSGI(
    schema,
    middleware=get_middlewares,
)
