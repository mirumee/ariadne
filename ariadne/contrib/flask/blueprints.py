import json
from ariadne import graphql_sync, combine_multipart_data
from ariadne.constants import PLAYGROUND_HTML
from flask import request, jsonify, current_app, Blueprint


graphql = Blueprint("graphql", __name__, url_prefix="/graphql")


@graphql.route("/", methods=["GET"])
def graphql_playground():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return PLAYGROUND_HTML, 200


@graphql.route("/", methods=["POST"])
def graphql_server():
    # GraphQL queries are always sent as POST
    if "application/json" in request.content_type:
        data = request.get_json()
    elif "multipart/form-data" in request.content_type:
        data = json.loads(request.form["operations"])
        files_map = json.loads(request.form["map"])
        data = combine_multipart_data(data, files_map, request.files)
    else:
        # Assume json content type if not specified
        data = request.get_json()

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        current_app.graphql_schema, data, context_value=request, debug=current_app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code
