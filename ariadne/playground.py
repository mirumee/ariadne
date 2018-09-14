import json
from typing import List, Union
from wsgiref.simple_server import make_server

from graphql import format_error, graphql

from .executable_schema import make_executable_schema

JSON_CONTENT_TYPE = "application/json"

PLAYGROUND_MINIMAL = """
<!DOCTYPE html>
<html>

<head>
  <meta charset=utf-8/>
  <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
  <title>GraphQL Playground</title>
  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react@1.7.0/build/static/css/index.css" />
  <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react@1.7.0/build/favicon.png" />
  <script src="//cdn.jsdelivr.net/npm/graphql-playground-react@1.7.0/build/static/js/middleware.js"></script>
</head>

<body>
  <div id="root">
    <style>
      body {
        background-color: rgb(23, 42, 58);
        font-family: Open Sans, sans-serif;
        height: 90vh;
      }

      #root {
        height: 100%;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .loading {
        font-size: 32px;
        font-weight: 200;
        color: rgba(255, 255, 255, .6);
        margin-left: 20px;
      }

      img {
        width: 78px;
        height: 78px;
      }

      .title {
        font-weight: 400;
      }
    </style>
    <img src='//cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png' alt=''>
    <div class="loading"> Loading
      <span class="title">GraphQL Playground</span>
    </div>
  </div>
  <script>window.addEventListener('load', function (event) {
      GraphQLPlayground.init(document.getElementById('root'), {
        // options as 'endpoint' belong here
      })
    })</script>
</body>

</html>
"""


class PlaygroundMiddleware:
    def __init__(
        self, app, type_defs: Union[str, List[str]], resolvers: dict, path: str = "/"
    ):
        self.app = (app,)
        self.path = path
        self.schema = make_executable_schema(type_defs, resolvers)

    def __call__(self, environ, start_response):
        if not environ["PATH_INFO"].startswith(self.path):
            return self.app(environ, start_response)

        if environ["REQUEST_METHOD"] == "GET":
            return self.handle_get(environ, start_response)
        if environ["REQUEST_METHOD"] == "POST":
            return self.handle_post(environ, start_response)

        return self.error_response(start_response, "405 Method Not Allowed")

    def error_response(self, start_response, status, message=None):
        start_response(status, [("Content-Type", "text/plain")])
        final_message = message or status
        return [final_message.encode("utf-8")]

    def handle_get(self, environ, start_response):
        start_response("200 OK", [("Content-Type", "text/html")])
        return [PLAYGROUND_MINIMAL.encode("utf-8")]

    def handle_post(self, environ, start_response):
        if environ["CONTENT_TYPE"] != JSON_CONTENT_TYPE:
            return self.error_response(
                start_response,
                "400 Bad Request",
                "Posted content must be of type {}".format(JSON_CONTENT_TYPE),
            )

        try:
            request_body_size = int(environ.get("CONTENT_LENGTH", 0))
        except ValueError:
            request_body_size = 0

        data = json.loads(environ["wsgi.input"].read(request_body_size))
        result = graphql(self.schema, data.get("query"), None, data.get("variables"))

        status = "200 OK"
        response = {}
        if result.errors:
            response["errors"] = [format_error(e) for e in result.errors]
        if result.invalid:
            status = "400 Bad Request"
        else:
            response["data"] = result.data

        start_response(status, [("Content-Type", JSON_CONTENT_TYPE)])
        return [json.dumps(response).encode("utf-8")]


def run_playground(type_defs: Union[str, List[str]], resolvers: dict, port: int = 8888):
    wsgi_app = PlaygroundMiddleware(None, type_defs, resolvers)
    srv = make_server("127.0.0.1", port, wsgi_app)
    srv.serve_forever()
