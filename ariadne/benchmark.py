import asyncio, random, string, statistics
from typing import List, Tuple

import httpx

from ariadne import ObjectType, QueryType, gql, make_executable_schema
from ariadne.asgi import GraphQL


def simple_query_formatter(queryname: string) -> string:
    name = """
    {
      %s{
        name,
        age
      }
    }
    """ % (
        queryname
    )
    return name


simple_query = {"query": simple_query_formatter("person")}
list_simple_query = {"query": simple_query_formatter("people")}


def measure_post_time(query, n: int = 100) -> Tuple:
    time_list = []
    for i in range(n):
        request = httpx.post("http://127.0.0.1:8000/", json=query)
        time_list.append(request.elapsed.microseconds / 1000)

    return {
        "min": min(time_list),
        "max": max(time_list),
        "avg": statistics.mean(time_list),
    }


def make_random_name_and_age(n: int) -> List[Tuple]:
    people_list = []
    for i in range(n):
        generate_name = random.sample(string.ascii_letters, 10)
        name = "".join(generate_name)
        age = random.randint(1, 99)
        people_list.append({"name": name, "age": age})
    return people_list


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

PEOPLE = make_random_name_and_age(500)
PERSON = [{"name": "John", "age": 23}]


@query.field("people")
def resolve_people(*_):
    return PEOPLE


@query.field("person")
def resolve_people(*_):
    return PERSON


schema = make_executable_schema(type_defs, query)

app = GraphQL(schema, debug=True)