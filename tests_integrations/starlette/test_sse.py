from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

from ariadne import SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
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

graphql = GraphQL(schema, http_handler=GraphQLHTTPSSEHandler())

app = Starlette(
    routes=[
        Route("/graphql", methods=["POST"], endpoint=graphql.handle_request),
        Mount("/mounted", graphql),
    ],
)

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
