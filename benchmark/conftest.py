import json
import os
from dataclasses import dataclass
from typing import List

import pytest

from ariadne import load_schema_from_path, make_executable_schema

BENCHMARK_DIR = os.path.dirname(__file__)


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


with open(os.path.join(BENCHMARK_DIR, "data.json")) as f:
    data = json.load(f)


def users_data():
    for row in data["users"]:
        group = Group(**row["group"])
        avatars = [Avatar(**avatar) for avatar in row["avatar"]]
        row = {**row, "avatar": avatars, "group": group}
        yield User(**row)


@pytest.fixture
def raw_data():
    return data


@pytest.fixture
def raw_data_one_item():
    return {"users": [data["users"][0]]}


@pytest.fixture
def hydrated_data():
    return list(users_data())


@pytest.fixture
def hydrated_data_one_item():
    for user in users_data():
        return [user]


@pytest.fixture
def type_defs():
    return load_schema_from_path(os.path.join(BENCHMARK_DIR, "schema.gql"))


@pytest.fixture
def schema(type_defs):
    return make_executable_schema(type_defs)
