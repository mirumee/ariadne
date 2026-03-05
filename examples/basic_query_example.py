"""
Example: Basic query with Ariadne and Starlette.

Run with:

    uvicorn examples.basic_query_example:app --reload

or:
    uv run --with "uvicorn[standard]" --with ariadne \\
        uvicorn examples.basic_query_example:app --reload
"""

from starlette.applications import Starlette

from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL

type_defs = """
    type Query {
        hello(name: String = "World"): String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(*_, name: str) -> str:
    return f"Hello, {name}!"


schema = make_executable_schema(type_defs, query)

app = Starlette()
graphql_app = GraphQL(schema, debug=True)
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
