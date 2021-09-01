import json

from fastapi.testclient import TestClient

from ariadne import QueryType, gql, make_executable_schema
from ariadne.asgi import GraphQL


def benchmark_simple_list(query: str):
    with open("benchmarks/simple.json") as f:
        data = json.load(f)

    app = GraphQL(schema, root_value=data)
    client = TestClient(app)
    request = client.post("/", json={"query": query})

    return request


def benchmark_simple(query: str):
    data = [{"name": "John", "age": 23}]
    app = GraphQL(schema, root_value=data)
    client = TestClient(app)
    request = client.post("/", json={"query": query})

    return request


def benchmark_complex_list(query: str):
    with open("benchmarks/complex.json", "r") as file:
        data = json.load(file)

    app = GraphQL(schema, root_value=data)
    client = TestClient(app)
    request = client.post("/", json={"query": query})

    return request


def benchmark_complex(query: str):
    data = [
        {
            "id": 1,
            "name": "John",
            "group": {"name": "name1", "roles": ["SEE"]},
            "avatar": [{"size": 123, "url": "http://127.0.0.1"}],
        }
    ]
    app = GraphQL(schema, root_value=data)
    client = TestClient(app)
    request = client.post("/", json={"query": query})

    return request


type_defs = gql(
    """
    type Query {
        people: [Person!]!
        person: [Person!]!
        users: [User!]
        user: [User!]
    }

    type Person {
        name: String
        age: Int
    }


    type User {
        id: ID!
        name: String!
        title: String
        group: Group!
        avatar: [Avatar!]!
    }

    type Group {
        name: String!
        roles: [Role!]!
    }

    type Avatar {
        size: Int!
        url: String!
    }

    enum Role {
        SEE
        BROWSE
        START
        REPLY
        MODERATE
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


@query.field("users")
def resolve_users(*_):
    with open("benchmarks/complex.json", "r") as file:
        data = json.load(file)
    return data


@query.field("user")
def resolve_user(*_):
    user = [
        {
            "id": 1,
            "name": "John",
            "group": {"name": "n1", "roles": ["SEE"]},
            "avatar": [{"size": 123, "url": "sdkasdoa"}],
        }
    ]
    return user


schema = make_executable_schema(type_defs, query)
