from attr import dataclass
import json
import pytest

from ariadne import QueryType, gql, make_executable_schema


@dataclass
class Person:
    name = "Name"
    age = 22


@dataclass
class User:
    id = 1234
    name = "Complexname"
    group = {"name": "Nameofgroup", "roles": ["SEE", "BROWSE"]}
    avatar = [{"size": 123, "url": "http://website.com"}]


query = QueryType()


@query.field("people")
def resolve_people(*_):
    with open("benchmarks/simple.json") as f:
        data = json.load(f)
    return data


@query.field("person")
def resolve_person(*_):
    return [Person]


@query.field("users")
def resolve_users(*_):
    with open("benchmarks/complex.json", "r") as file:
        data = json.load(file)
    return data


@query.field("user")
def resolve_user(*_):
    return [User]


@pytest.fixture
def type_defs():
    with open("benchmarks/schema.gql") as file:
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
def complex_query_list():
    query = """
    {
        users{
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
    return query


@pytest.fixture
def complex_query():
    query = """
    {
        user{
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
    return query


@pytest.fixture
def simple_query_list():
    query = """
    {
      people{
        name,
        age
      }
    }
    """
    return query


@pytest.fixture
def simple_query():
    query = """
    {
      person{
        name
        age
      }
    }
    """
    return query
