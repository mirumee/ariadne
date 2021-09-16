from attr import dataclass
import json
import pytest
from typing import List

from ariadne import gql, make_executable_schema, QueryType


@dataclass
class Group:
    name: str
    roles: list


@dataclass
class Avatar:
    size: int
    url: str


@dataclass
class User:
    id: int
    name: str
    group: Group
    avatar: List[Avatar]


with open("benchmarks/data.json") as f:
    data = json.load(f)


def users_data():
    for row in data["users"]:
        yield User(**row)


@pytest.fixture
def raw_data():
    return data


@pytest.fixture
def raw_data_one_element():
    return {"users": [data["users"][0]]}


@pytest.fixture
def hydrated_data():
    return [user for user in users_data()]


@pytest.fixture
def hydrated_data_one_element():
    for user in users_data():
        return [user]


query = QueryType()


@pytest.fixture
def type_defs():
    with open("benchmarks/schema.gql", "r") as file:
        schema = gql(file.read())
    return schema


@pytest.fixture
def schema(type_defs):
    return make_executable_schema(type_defs, query)
