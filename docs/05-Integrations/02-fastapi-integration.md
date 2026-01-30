---
id: fastapi-integration
title: FastAPI integration
sidebar_label: FastAPI
---

## Mounting ASGI application

Ariadne is an ASGI application that can be mounted under FastAPI. It will support both HTTP and WebSocket traffic used by subscriptions:

```python
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import FastAPI

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

# Mount Ariadne GraphQL as sub-application for FastAPI
app = FastAPI()

app.mount("/graphql/", GraphQL(schema, debug=True))
```

## GraphQL routes

`GraphQL` provides methods that can be used in FastAPI routes:

```python
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler
from fastapi import FastAPI, Depends, Request
from fastapi.websockets import WebSocket
from myapp.database import get_database_session

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

# Custom context setup method
def get_context_value(request_or_ws: Request | WebSocket, _data) -> dict:
    return {
        "request": request_or_ws,
        "db": request_or_ws.scope["db"],
    }

# Create GraphQL App instance
graphql_app = GraphQL(
    schema,
    debug=True,
    context_value=get_context_value,
    websocket_handler=GraphQLTransportWSHandler(),
)

# Create FastAPI instance
app = FastAPI()


# Handle GET requests to serve GraphQL explorer
# Handle OPTIONS requests for CORS
@app.get("/graphql/")
@app.options("/graphql/")
async def handle_graphql_explorer(request: Request):
    return await graphql_app.handle_request(request)

# Handle POST requests to execute GraphQL queries
@app.post("/graphql/")
async def handle_graphql_query(
    request: Request,
    db = Depends(get_database_session),
):
    # Expose database connection to the GraphQL through request's scope
    request.scope["db"] = db
    return await graphql_app.handle_request(request)


# Handle GraphQL subscriptions over websocket
@app.websocket("/graphql")
async def graphql_subscriptions(
    websocket: WebSocket,
    db = Depends(get_database_session),
):
    # Expose database connection to the GraphQL through request's scope
    websocket.scope["db"] = db
    await graphql_app.handle_websocket(websocket)
```
