"""
Example: Mutations and input types with an in-memory store.

Run with:

    uvicorn examples.mutation_example:app --reload

or:
    uv run --with "uvicorn[standard]" --with ariadne \\
        uvicorn examples.mutation_example:app --reload
"""

from starlette.applications import Starlette

from ariadne import MutationType, QueryType, make_executable_schema
from ariadne.asgi import GraphQL

type_defs = """
    type Query {
        todos: [Todo!]!
    }

    type Mutation {
        addTodo(input: AddTodoInput!): Todo!
        toggleTodo(id: ID!): Todo
    }

    input AddTodoInput {
        title: String!
        completed: Boolean = false
    }

    type Todo {
        id: ID!
        title: String!
        completed: Boolean!
    }
"""

query = QueryType()
mutation = MutationType()

TODOS: list[dict[str, object]] = []
NEXT_ID = 1


@query.field("todos")
def resolve_todos(*_):
    return TODOS


@mutation.field("addTodo")
def resolve_add_todo(*_, input: dict) -> dict:
    global NEXT_ID

    todo = {
        "id": str(NEXT_ID),
        "title": input["title"],
        "completed": bool(input.get("completed", False)),
    }
    NEXT_ID += 1
    TODOS.append(todo)
    return todo


@mutation.field("toggleTodo")
def resolve_toggle_todo(*_, id: str) -> dict | None:
    for todo in TODOS:
        if todo["id"] == str(id):
            todo["completed"] = not bool(todo["completed"])
            return todo
    return None


schema = make_executable_schema(type_defs, [query, mutation])

app = Starlette()
graphql_app = GraphQL(schema, debug=True)
app.mount("/graphql", graphql_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
