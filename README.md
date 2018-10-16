# Ariadne

[![Build Status](https://travis-ci.org/mirumee/ariadne.svg?branch=master)](https://travis-ci.org/mirumee/ariadne)
[![codecov](https://codecov.io/gh/mirumee/ariadne/branch/master/graph/badge.svg)](https://codecov.io/gh/mirumee/ariadne)

Ariadne is a Python library for implementing [GraphQL](http://graphql.github.io/) servers, inspired by [Apollo Server](https://www.apollographql.com/docs/apollo-server/) and built with [GraphQL-core](https://github.com/graphql-python/graphql-core).

**Warning**: The work on library is currently in experimental phase. We invite you to give Ariadne a try, but if you are looking to build production-ready GraphQL API, please use more stable solutions such as [Graphene](https://github.com/graphql-python/graphene).

## Quickstart 

Following example creates API defining `Person` type and single query field `people` returning list of two persons. It also starts local dev server with [GraphQL Playground](https://github.com/prisma/graphql-playground) available on the `http://127.0.0.1:8888` address.

```python
from ariadne import GraphQLMiddleware

# Define types using Schema Definition Language (https://graphql.org/learn/schema/)
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


# Resolvers are simple python functions
def resolve_people(*_):
    return [
        {"firstName": "John", "lastName": "Doe", "age": 21},
        {"firstName": "Bob", "lastName": "Boberson", "age": 24},
    ]


def resolve_person_fullname(person, *_):
    return "%s %s" % (person["firstName"], person["lastName"])


# Map resolver functions to type fields using dict
resolvers = {
    "Query": {"people": resolve_people},
    "Person": {"fullName": resolve_person_fullname},
}


# Create and run dev server that provides api browser
graphql_server = GraphQLMiddleware.make_simple_server(type_defs, resolvers)
graphql_server.serve_forever()  # Visit http://127.0.0.1:8888 to see API browser!
```
