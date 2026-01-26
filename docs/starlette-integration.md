---
id: starlette-integration
title: Starlette integration
sidebar_label: Starlette
---


## Mounting ASGI application

Ariadne is an ASGI application that can be mounted under Starlette. It will support both HTTP and WebSocket traffic used by subscriptions:

```python
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from starlette.applications import Starlette

type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(*_):
    return "Hello world!"


# Create executable schema instance
schema = make_executable_schema(type_defs, query)

# Mount Ariadne GraphQL as sub-application for Starlette
app = Starlette(debug=True)

app.mount("/graphql/", GraphQL(schema, debug=True))
```


## Using routes

`GraphQL` provides methods that can be used as Starlette routes:

```python
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute

type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(*_):
    return "Hello world!"


# Create executable schema instance
schema = make_executable_schema(type_defs, query)

# Create GraphQL App instance
graphql_app = GraphQL(
    schema,
    debug=True,
    websocket_handler=GraphQLTransportWSHandler(),
)

# Create Starlette App instance using method handlers from GraphQL as endpoints
app = Starlette(
    routes=[
        Route("/graphql/", graphql_app.handle_request, methods=["GET", "POST", "OPTIONS"]),
        WebSocketRoute("/graphql/", graphql_app.handle_websocket),
    ],
)
```


## Using in custom routes

You can wrap Starlette routes in custom logic if you want to. This enables passing additional data or objects to the GraphQL through `request.scope`:

```python
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute

type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(*_):
    return "Hello world!"


# Create executable schema instance
schema = make_executable_schema(type_defs, query)

# Create GraphQL App instance
graphql_app = GraphQL(
    schema,
    debug=True,
    websocket_handler=GraphQLTransportWSHandler(),
)


# Create custom routes wrapping default ones provided by Ariadne
async def graphql_route(request):
    # Insert custom logic there
    # For example, check if user is authenticated before displaying Playground
    # Or pass something to GraphQL through request.scope
    return await graphql_app.handle_request(request)


async def websocket_route(websocket):
    # Insert custom logic there
    await graphql_app.handle_websocket(websocket)


# Create Starlette App instance using custom routes
app = Starlette(
    routes=[
        Route("/graphql/", graphql_route, methods=["GET", "POST", "OPTIONS"]),
        WebSocketRoute("/graphql/", graphql_app.handle_websocket),
    ],
)
```
