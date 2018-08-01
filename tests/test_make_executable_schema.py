from datetime import date

from ariadne import execute_request, make_executable_schema


TEST_TYPE_DEFS = """
    schema {
        query: Query
    }

    scalar Date

    type Query {
        word: String
        today: Date
        person: Person
        persons: [Person]!
    }

    type Person {
        firstName: String
        lastName: String
        fullName: String
    }
"""


def resolve_date(date):
    return date.strftime('%Y-%m-%d')


def resolve_word(*_):
    return "Hello!"


def resolve_today(*_):
    return date.today()


def resolve_person(*_):
    return {"firstName": "John", "lastName": "Doe"}


def resolve_persons(*_):
    return [
        {"firstName": "John", "lastName": "Doe"},
        {"firstName": "Bob", "lastName": "Bobertson"},
    ]


def resolve_person_fullname(person, *_):
    return "%s %s" % (person["firstName"], person["lastName"])


TEST_RESOLVERS = {
    "Query": {
        "word": resolve_word,
        "today": resolve_today,
        "person": resolve_person,
        "persons": resolve_persons,
    },
    "Date": resolve_date,
    "Person": {"fullName": resolve_person_fullname},
}


TEST_QUERY = """
    query testExecutableSchema {
        word
        today
        person {
            firstName
            lastName
            fullName
        }
        persons {
            firstName
            lastName
            fullName
        }
    }
"""


def test_query_executable_schema():
    schema = make_executable_schema(TEST_TYPE_DEFS, TEST_RESOLVERS)
    result = execute_request(schema, TEST_QUERY)

    assert result.data == {
        "word": "Hello!",
        "today": date.today().strftime('%Y-%m-%d'),
        "person": {"firstName": "John", "lastName": "Doe", "fullName": "John Doe"},
        "persons": [
            {"firstName": "John", "lastName": "Doe", "fullName": "John Doe"},
            {"firstName": "Bob", "lastName": "Bobertson", "fullName": "Bob Bobertson"},
        ],
    }
