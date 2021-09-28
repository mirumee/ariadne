from attr import dataclass
import json
import pytest
from typing import List

from ariadne import load_schema_from_path, make_executable_schema, QueryType


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
        group = Group(**row.get("group"))
        avatars = [Avatar(**avatar) for avatar in row.get("avatar")]
        row = {**row, "avatar": avatars, "group": group}
        yield User(**row)


@pytest.fixture
def raw_data():
    return data


@pytest.fixture
def raw_data_one_element():
    return {"users": [data["users"][0]]}


@pytest.fixture
def hydrated_data():
    return list(users_data())


@pytest.fixture
def hydrated_data_one_element():
    for user in users_data():
        return [user]


query = QueryType()


@pytest.fixture
def type_defs():
    return load_schema_from_path("benchmarks/schema.gql")


@pytest.fixture
def schema(type_defs):
    return make_executable_schema(type_defs, query)
