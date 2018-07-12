from ariadne import build_schema, execute_request, make_executable_schema


TEST_SCHEMA = """
schema {
    query: Query
}

type Query {
    person: Person
}

type Person {
    firstName: String
    lastName: String
    fullName: String
}
"""

TEST_QUERY = """
query {
    person {
        fullName
    }
}
"""


def resolve_person(*_):
    return {'firstName': 'John', 'lastName': 'Doe'}


def resolve_person_fullname(person, *_):
    return '%s %s' % (person['firstName'], person['lastName'])


TEST_RESOLVERS = {
    'Query': {
        'person': resolve_person
    },
    'Person': {
        'fullName': resolve_person_fullname
    }
}


def test_schema_query():
    schema = build_schema(TEST_SCHEMA)
    make_executable_schema(schema, TEST_RESOLVERS)
    result = execute_request(schema, TEST_QUERY)

    assert result.data == {'person': {'fullName': 'John Doe'}}
