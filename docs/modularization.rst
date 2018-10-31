Modularization
==============

Ariadne allows you to spread your GraphQL API implementation over multiple Python modules.

Types can be defined as list of strings instead of one large string and resolvers can be defined as list of dicts of dicts for same effect. Here is example of API that moves scalars and ``User`` to dedicated modules::

    # graphqlapi.py
    from ariadne import GraphQLMiddleware
    from . import scalars, users

    # Defining Query and Mutation types in root module is optional
    # but makes it easier to see what features are implemented by the API
    # without having to run and introspect it with GraphQL Playground.
    root_type_defs = """
        type Query {
            users: [Users!]
        }
    """

    graphql_server = GraphQLMiddleware.make_simple_server(
        [root_type_defs, scalars.type_defs, users.type_defs],
        [scalars.resolvers, users.resolvers]
    )

    # scalars.py
    type_defs = """
        scalar Date
        scalar Datetime
    """

    resolvers = {
        "Date": {},
        "Datetime": {},
    }

    # users.py
    type_defs = """
        type User {
            username: String!
            joinedOn: Date!
            lastVisitOn: Datetime
        }
    """


    def resolve_users(*_):
        return get_some_users()


    resolvers = {
        "User": {},  # User resolvers will be merged with other resolvers
        "Query": {
            "users": resolve_users, # Add resolvers for root type too
        },
    }