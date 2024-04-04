from http import HTTPStatus

from flask import Flask, jsonify, request

from ariadne import graphql_sync, make_executable_schema
from ariadne.explorer import ExplorerGraphiQL

schema = make_executable_schema(
    """
    type Query {
        hello: String!
    }
    """
)


app = Flask(__name__)
app.config.update(
    {
        "TESTING": True,
    }
)


explorer = ExplorerGraphiQL(title="My Flask GraphQL")


@app.route("/graphql", methods=["GET"])
def graphql_playground():
    html = explorer.html(request)
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return html, 200


@app.route("/graphql", methods=["POST"])
def graphql_server():
    # GraphQL queries are always sent as POST
    data = request.get_json()

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        schema,
        data,
        context_value={"request": request},
        root_value={"hello": "Hello Flask!"},
        debug=app.debug,
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code


client = app.test_client()


def test_execute_graphql_query_on_post_request():
    response = client.post("/graphql", json={"query": "{ hello }"})
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        "data": {
            "hello": "Hello Flask!",
        },
    }


def test_return_api_explorer_on_get_request():
    response = client.get("/graphql")
    assert response.status_code == HTTPStatus.OK
    assert b"graphiql" in response.data
