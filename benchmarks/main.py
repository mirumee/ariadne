import json
from typing import Tuple

from fastapi.testclient import TestClient

from ariadne import QueryType, gql, make_executable_schema
from ariadne.asgi import GraphQL


def benchmark_simple_list(query: str) -> Tuple:
    with open("benchmarks/simple.json") as f:
        data = json.load(f)

    app = GraphQL(schema, root_value=data)
    client = TestClient(app)
    request = client.post("/", json={"query": query})

    return request.status_code


def benchmark_simple(query: str) -> Tuple:
    data = [{"name": "John", "age": 23}]
    app = GraphQL(schema, root_value=data)
    client = TestClient(app)
    request = client.post("/", json={"query": query})

    return request.status_code


type_defs = gql(
    """
    type Query {
        people: [Person!]!
        person: [Person!]!
    }

    type Person {
        name: String
        age: Int
    }
"""
)

query = QueryType()


@query.field("people")
def resolve_people(*_):
    with open("benchmarks/simple.json") as f:
        data = json.load(f)
    return data


@query.field("person")
def resolve_person(*_):
    return [{"name": "John", "age": 23}]


schema = make_executable_schema(type_defs, query)
