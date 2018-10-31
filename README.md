![Ariadne](https://ariadne.readthedocs.io/en/latest/_images/logo.png)

[![Documentation](https://readthedocs.org/projects/ariadne/badge/?version=latest)](https://ariadne.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/mirumee/ariadne.svg?branch=master)](https://travis-ci.org/mirumee/ariadne)
[![Codecov](https://codecov.io/gh/mirumee/ariadne/branch/master/graph/badge.svg)](https://codecov.io/gh/mirumee/ariadne)

- - - - -

# Ariadne

Ariadne is a Python library for implementing [GraphQL](http://graphql.github.io/) servers, inspired by [Apollo Server](https://www.apollographql.com/docs/apollo-server/) and built with [GraphQL-core](https://github.com/graphql-python/graphql-core).

Currently the library already implements enough features to enable developers to build functional GraphQL APIs. It is also being dogfooded internally at number of projects.

Documentation is available [here](https://ariadne.readthedocs.io/en/latest/?badge=latest).


## Installation

Ariadne can be installed with pip:

    pip install ariadne


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

For more guides and examples, please see the [documentation](https://ariadne.readthedocs.io/en/latest/?badge=latest).


Contributing
------------

We are welcoming contributions to Ariadne! If you've found a bug, issue, got question or just want to drop general feedback, feel free to use [GitHub issues](https://github.com/mirumee/ariadne/issues).

For guidance and instructions, please see [CONTRIBUTING.md](CONTRIBUTING.md).
