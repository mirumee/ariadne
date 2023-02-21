[![Ariadne](https://ariadnegraphql.org/img/logo-horizontal-sm.png)](https://ariadnegraphql.org)

[![Documentation](https://img.shields.io/badge/docs-ariadnegraphql.org-brightgreen.svg)](https://ariadnegraphql.org)
[![Codecov](https://codecov.io/gh/mirumee/ariadne/branch/master/graph/badge.svg)](https://codecov.io/gh/mirumee/ariadne)

- - - - -

# Ariadne

Ariadne is a Python library for implementing [GraphQL](http://graphql.github.io/) servers.

- **Schema-first:** Ariadne enables Python developers to use schema-first approach to the API implementation. This is the leading approach used by the GraphQL community and supported by dozens of frontend and backend developer tools, examples, and learning resources. Ariadne makes all of this immediately available to you and other members of your team.
- **Simple:** Ariadne offers small, consistent and easy to memorize API that lets developers focus on business problems, not the boilerplate.
- **Open:** Ariadne was designed to be modular and open for customization. If you are missing or unhappy with something, extend or easily swap with your own.

Documentation is available [here](https://ariadnegraphql.org).


## Features

- Simple, quick to learn and easy to memorize API.
- Compatibility with GraphQL.js version 15.5.1.
- Queries, mutations and input types.
- Asynchronous resolvers and query execution.
- Subscriptions.
- Custom scalars, enums and schema directives.
- Unions and interfaces.
- File uploads.
- Defining schema using SDL strings.
- Loading schema from `.graphql`, `.gql`, and `.graphqls` files.
- WSGI middleware for implementing GraphQL in existing sites.
- Apollo Tracing and [OpenTracing](http://opentracing.io) extensions for API monitoring.
- Opt-in automatic resolvers mapping between `camelCase` and `snake_case`, and a `@convert_kwargs_to_snake_case` function decorator for converting `camelCase` kwargs to `snake_case`.
- Built-in simple synchronous dev server for quick GraphQL experimentation and GraphQL Playground.
- Support for [Apollo GraphQL extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=apollographql.vscode-apollo).
- GraphQL syntax validation via `gql()` helper function. Also provides colorization if Apollo GraphQL extension is installed.
- No global state or object registry, support for multiple GraphQL APIs in same codebase with explicit type reuse.
- Support for `Apollo Federation`.


## Installation

Ariadne can be installed with pip:

```console
pip install ariadne
```

Ariadne requires Python 3.7 or higher.


## Quickstart

The following example creates an API defining `Person` type and single query field `people` returning a list of two persons. It also starts a local dev server with [GraphQL Playground](https://github.com/prisma/graphql-playground) available on the `http://127.0.0.1:8000` address.

Start by installing [uvicorn](http://www.uvicorn.org/), an ASGI server we will use to serve the API:

```console
pip install uvicorn
```

Then create an `example.py` file for your example application:

```python
from ariadne import ObjectType, QueryType, gql, make_executable_schema
from ariadne.asgi import GraphQL

# Define types using Schema Definition Language (https://graphql.org/learn/schema/)
# Wrapping string in gql function provides validation and better error traceback
type_defs = gql("""
    type Query {
        people: [Person!]!
    }

    type Person {
        firstName: String
        lastName: String
        age: Int
        fullName: String
    }
""")

# Map resolver functions to Query fields using QueryType
query = QueryType()

# Resolvers are simple python functions
@query.field("people")
def resolve_people(*_):
    return [
        {"firstName": "John", "lastName": "Doe", "age": 21},
        {"firstName": "Bob", "lastName": "Boberson", "age": 24},
    ]


# Map resolver functions to custom type fields using ObjectType
person = ObjectType("Person")

@person.field("fullName")
def resolve_person_fullname(person, *_):
    return "%s %s" % (person["firstName"], person["lastName"])

# Create executable GraphQL schema
schema = make_executable_schema(type_defs, query, person)

# Create an ASGI app using the schema, running in debug mode
app = GraphQL(schema, debug=True)
```

Finally run the server:

```console
uvicorn example:app
```

For more guides and examples, please see the [documentation](https://ariadnegraphql.org).


## Contributing

We are welcoming contributions to Ariadne! If you've found a bug or issue, feel free to use [GitHub issues](https://github.com/mirumee/ariadne/issues). If you have any questions or feedback, don't hesitate to catch us on [GitHub discussions](https://github.com/mirumee/ariadne/discussions/).

For guidance and instructions, please see [CONTRIBUTING.md](CONTRIBUTING.md).

Website and the docs have their own GitHub repository: [mirumee/ariadne-website](https://github.com/mirumee/ariadne-website)

Also make sure you follow [@AriadneGraphQL](https://twitter.com/AriadneGraphQL) on Twitter for latest updates, news and random musings!

**Crafted with ❤️ by [Mirumee Software](http://mirumee.com)**
hello@mirumee.com
