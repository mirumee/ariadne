"""
Example: Flask integration.

This example uses Ariadne with Flask and `graphql_sync`.

Run with:

    python examples/flask_integration_example.py

or:
    uv run --with "uvicorn[standard]" --with ariadne --with flask \\
        python examples/flask_integration_example.py
"""

from flask import Flask, jsonify, request

from ariadne import QueryType, graphql_sync, make_executable_schema
from ariadne.explorer import ExplorerGraphiQL

type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()


@query.field("hello")
def resolve_hello(_, info):
    flask_request = info.context
    user_agent = flask_request.headers.get("User-Agent", "Guest")
    return f"Hello, {user_agent}!"


schema = make_executable_schema(type_defs, query)

app = Flask(__name__)

# Retrieve HTML for the GraphiQL explorer once at startup.
explorer_html = ExplorerGraphiQL().html(None)


@app.route("/graphql", methods=["GET"])
def graphql_explorer():
    return explorer_html, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()

    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug,
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(debug=True)
