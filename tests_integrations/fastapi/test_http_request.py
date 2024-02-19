from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from fastapi import FastAPI, Request
from starlette.testclient import TestClient


schema = make_executable_schema(
    """
    type Query {
        hello: String!
    }
    """
)


app = FastAPI()
graphql = GraphQL(schema, root_value={"hello": "Hello FastAPI!"})


@app.post("/graphql")
async def graphql_route(request: Request):
    return await graphql.handle_request(request)


app.mount("/mounted", graphql)


client = TestClient(app, backend="asyncio")


def test_run_graphql_query_through_route():
    response = client.post("/graphql", json={"query": "{ hello }"})
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "hello": "Hello FastAPI!",
        },
    }


def test_run_graphql_query_through_mount():
    response = client.post("/mounted/", json={"query": "{ hello }"})
    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "hello": "Hello FastAPI!",
        },
    }
