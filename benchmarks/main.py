import json
import statistics
from typing import List, Tuple

from fastapi.testclient import TestClient

from ariadne import QueryType, gql, make_executable_schema
from ariadne.asgi import GraphQL


def benchmark_simple(query, n:int = 10) -> Tuple:
    with open('benchmarks/simple.json') as f:
        data = json.load(f)

    app = GraphQL(schema, root_value=data)

    client = TestClient(app)

    time_list = []
    for _ in range(n):
        request = client.post("/", data=query)
        time_list.append(request.elapsed.microseconds / 1000)

    return {
        "min": min(time_list),
        "max": max(time_list),
        "avg": statistics.mean(time_list),
    }


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

simple_query_list = """
    {
      people{
        name,
        age
      }
    }
    """

schema = make_executable_schema(type_defs, query)


def main():
    print(benchmark_simple(simple_query_list))


if __name__== "__main__":
    main()

