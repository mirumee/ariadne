import json
import pytest

from ariadne import QueryType, gql, make_executable_schema


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


@pytest.fixture
def type_defs():
    with open("benchmarks/schema.gql") as f:
        schema = gql(f.read())
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
