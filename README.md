# Ariadne

[![Build Status](https://travis-ci.org/mirumee/ariadne.svg?branch=master)](https://travis-ci.org/mirumee/ariadne)
[![codecov](https://codecov.io/gh/mirumee/ariadne/branch/master/graph/badge.svg)](https://codecov.io/gh/mirumee/ariadne)

Ariadne is a Python library for implementing [GraphQL](http://graphql.github.io/) servers, inspired by [Apollo Server](https://www.apollographql.com/docs/apollo-server/) and built with [GraphQL-core](https://github.com/graphql-python/graphql-core).

**Warning**: The work on library is currently in experimental phase. We invite you to give Ariadne a try, but if you are looking to build production-ready GraphQL API, please use more stable solutions such as [Graphene](https://github.com/graphql-python/graphene).

## Quickstart 

```python
from ariadne import make_executable_schema
from graphql import graphql

type_defs = """
    type Query {
        people: [Person!]!
    }

    type Person {
        firstName: String
        lastName: String
        age: Int
        fullName: String
    }
"""


def resolve_people(*_):
    return [
        {"firstName": "John", "lastName": "Doe", "age": 21},
        {"firstName": "Bob", "lastName": "Boberson", "age": 24},
    ]


def resolve_person_fullname(person, *_):
    return "%s %s" % (person["firstName"], person["lastName"])


resolvers = {
    "Query": {"people": resolve_people},
    "Person": {"fullName": resolve_person_fullname},
}


schema = make_executable_schema(type_defs, resolvers)

query = """
    query getPeople {
        people {
            firstName
            fullName
            age
        }
    }
"""

result = graphql(schema, query)

assert result.data == {
    "people": [
        {"firstName": "John", "fullName": "John Doe", "age": 21},
        {"firstName": "Bob", "fullName": "Bob Boberson", "age": 24},
    ]
}
```
