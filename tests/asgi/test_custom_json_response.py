import json
from typing import Any, Dict, Type

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
    class CustomGraphQL(GraphQL):
        def build_json_response(
            self,
            content: Dict[str, Any],
            status_code: int
        ) -> Type[JSONResponse]:
            return PrettyJSONResponse(content, status_code=status_code)
    
    return CustomGraphQL(schema)


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
