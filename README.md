# Ariadne

[![Build Status](https://travis-ci.org/mirumee/ariadne.svg?branch=master)](https://travis-ci.org/mirumee/ariadne)
[![codecov](https://codecov.io/gh/mirumee/ariadne/branch/master/graph/badge.svg)](https://codecov.io/gh/mirumee/ariadne)

Ariadne is a Python library for implementing [GraphQL](http://graphql.github.io/) servers, inspired by [Apollo Server](http://graphql.github.io/) and built with [GraphQL-core](https://github.com/graphql-python/graphql-core).

**Warning**: The work on library is currently in experimental phase. We invite you to give Ariadne a try, but if you are looking to build production-ready GraphQL API, please use more stable solutions such as [Graphene](https://github.com/graphql-python/graphene).

## Quickstart 

```python
from ariadne import execute_request, make_executable_schema


type_defs = """
    schema {
        query Query
    }

    type Query {
        persons [Person]!
    }

    type Person {
        firstName String
        secondName String
        age Int
        fullName String
    }
"""


def resolve_persons(*_):
    return [
        {"firstName": "John", "lastName": "Doe", "age": 21},
        {"firstName": "Bob", "lastName": "Boberson", "age": 24},
    ]


def resolve_person_fullname(person, *_):
    return "%s %s" % (person["firstName"], person["lastName"])


resolvers = {
    "Query": {"person": resolve_person},
    "Person": {"fullName": resolve_person_fullname},
}


schema = make_executable_schema(type_defs, resolvers)

query = """
    query getPersons {
        persons {
            firstName
            fullName
            age
        }
    }
"""

result = execute_request(schema, query)

assert result.data == [
    {"firstName": "John", "fullName": "John, Doe", "age": 21},
    {"firstName": "Bob", "fullName": "Bob, Boberson", "age": 24},
]
```