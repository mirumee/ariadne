"""
Example: FastAPI integration.

This example mounts Ariadne's ASGI GraphQL app under FastAPI.

Run with:

    uvicorn examples.fastapi_integration_example:app --reload

or:
    uv run --with "uvicorn[standard]" --with ariadne --with fastapi \\
        uvicorn examples.fastapi_integration_example:app --reload
"""

from fastapi import FastAPI

from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL

type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(*_):
    return "Hello from FastAPI!"


schema = make_executable_schema(type_defs, query)

app = FastAPI()
graphql_app = GraphQL(schema, debug=True)
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
