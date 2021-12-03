import json
from typing import Any

import pytest
from starlette.responses import JSONResponse

from ariadne.asgi import GraphQL


operation_name = "SayHello"
variables = {"name": "Bob"}
complex_query = """
  query SayHello($name: String!) {
    hello(name: $name)
  }
"""


class PrettyJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(content, indent=4).encode("utf-8")


@pytest.fixture
def app(schema):
    return GraphQL(schema, json_response_class=PrettyJSONResponse)


def test_custom_json_response(client):
    response = client.post(
        "/",
        json={
            "query": complex_query,
            "variables": variables,
            "operationName": operation_name,
        },
    )

    expected_json = {"data": {"hello": "Hello, Bob!"}}
    assert response.text == json.dumps(expected_json, indent=4)
