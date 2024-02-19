from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient


schema = make_executable_schema(
    """
    type Query {
        hello: String!
    }
    """
)

graphql = GraphQL(schema, root_value={"hello": "Hello Starlette!"})


app = Starlette(
    routes=[
        Route("/graphql", graphql.handle_request, methods=["GET", "POST"]),
        Mount("/mounted", graphql),
    ],
)


client = TestClient(app, backend="asyncio")


def test_run_graphql_query_through_route():
    response = client.post("/graphql", json={"query": "{ hello }"})
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "hello": "Hello Starlette!",
        },
    }


def test_run_graphql_query_through_mount():
    response = client.post("/mounted/", json={"query": "{ hello }"})
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "hello": "Hello Starlette!",
        },
    }
