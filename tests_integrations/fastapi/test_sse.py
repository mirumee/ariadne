from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler
from ariadne.contrib.sse import GraphQLHTTPSSEHandler

subscription_type = SubscriptionType()


@subscription_type.source("counter")
async def counter_source(*_):
    yield 1


@subscription_type.field("counter")
async def counter_resolve(obj, *_):
    return obj


schema = make_executable_schema(
    """
    type Query {
        _unused: String
    }

    type Subscription {
        counter: Int!
    }
    """,
    subscription_type,
)

app = FastAPI()
graphql = GraphQL(
    schema,
    http_handler=GraphQLHTTPSSEHandler(),
    websocket_handler=GraphQLTransportWSHandler(),
)


@app.post("/graphql")
async def graphql_route(request: Request):
    return await graphql.handle_request(request)


app.mount("/mounted", graphql)

client = TestClient(app, headers={"Accept": "text/event-stream"})


def test_run_graphql_subscription_through_route():
    response = client.post(
        "/graphql",
        json={
            "operationName": None,
            "query": "subscription { counter }",
            "variables": None,
        },
    )

    assert response.status_code == 200
    assert '{"data": {"counter": 1}}' in response.text


def test_run_graphql_subscription_through_mount():
    response = client.post(
        "/mounted",
        json={
            "operationName": None,
            "query": "subscription { counter }",
            "variables": None,
        },
    )

    assert response.status_code == 200
    assert '{"data": {"counter": 1}}' in response.text
