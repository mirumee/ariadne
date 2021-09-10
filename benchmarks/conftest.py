from attr import dataclass
import json
import pytest

from ariadne import QueryType, gql, make_executable_schema


@dataclass
class Person:
    name: str
    age: int


@dataclass
class User:
    id: int
    name: str
    group: dict
    avatar: list


with open("benchmarks/simple.json") as f:
    simple_data = json.load(f)

with open("benchmarks/complex.json") as f:
    complex_data = json.load(f)


def person_data_dictionary():
    person = simple_data[0]
    return {"name": person["name"], "age": person["age"]}


def user_data_dictionary():
    user = complex_data[0]
    return {"name": user["name"], "group": user["group"], "avatar": user["avatar"]}


query = QueryType()


@query.field("people_dataclass")
def resolve_people_dataclass(*_):
    for row in simple_data:
        yield Person(**row)


@query.field("person_dataclass")
def resolve_person_dataclass(*_):
    for row in simple_data:
        return [Person(**row)]


@query.field("people")
def resolve_people(*_):
    return simple_data


@query.field("person")
def resolve_person(*_):
    return [person_data_dictionary()]


@query.field("users_dataclass")
def resolve_users_dataclass(*_):
    for row in complex_data:
        yield User(**row)


@query.field("user_dataclass")
def resolve_user_dataclass(*_):
    for row in complex_data:
        return [User(**row)]


@query.field("users")
def resolve_users(*_):
    return complex_data


@query.field("user")
def resolve_user(*_):
    return [user_data_dictionary()]


@pytest.fixture
def type_defs():
    with open("benchmarks/schema.gql", "r") as file:
        schema = gql(file.read())
    return schema


@pytest.fixture
def schema(type_defs):
    return make_executable_schema(type_defs, query)


@pytest.fixture
def simple_data_from_json():
    with open("benchmarks/simple.json", "r") as file:
        return json.load(file)


@pytest.fixture
def complex_data_from_json():
    with open("benchmarks/complex.json", "r") as file:
        return json.load(file)


@pytest.fixture
def complex_query():
    def name_of_query(name: str):
        query = (
            """
        {
            %s{
                name
                group{
                    name
                    roles
                }
                avatar{
                    size
                    url
                }
            }
        }
        """
            % name
        )
        return query

    return name_of_query


@pytest.fixture
def simple_query():
    def name_of_query(name: str):
        query = (
            """
        {
        %s{
            name
            age
        }
        }
        """
            % name
        )
        return query

    return name_of_query
