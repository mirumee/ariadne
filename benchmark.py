import random
import string
import statistics
import threading
from typing import List, Tuple

import httpx
import uvicorn 

from ariadne import QueryType, gql, make_executable_schema
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


def measure_post_time(query, n: int = 10) -> Tuple:
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
    for _ in range(n):
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

def post_after_server_start(n: int = 10):
    result_list = []
    result_list.append(measure_post_time(simple_query, n))
    result_list.append(measure_post_time(list_simple_query, n))

    print(result_list)
    return result_list


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == '__main__':
    t1 = threading.Thread(target=start_server)
    t2 = threading.Thread(target=post_after_server_start)
    
    t1.start()
    t2.start()
