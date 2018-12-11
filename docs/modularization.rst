Modularization
==============

Ariadne allows you to spread your GraphQL API implementation over multiple files, with different strategies being avilable for schema and resolvers.

Types can be defined as list of strings instead of one large string and resolvers can be defined as list of ``ResolverMap`` for same effect. Here is example of API that moves scalars and ``User`` to dedicated modules::

    # graphqlapi.py
    from ariadne import GraphQLMiddleware
    from . import scalars, users

    # Defining Query and Mutation types in root module is required,
    # because its impossible to redefine type in submodule.
    # All other types may be defined at modules and imported.
    root_type_defs = """
        type Query {
            users: [Users!]
        }
    """

    graphql_server = GraphQLMiddleware.make_simple_server(
        [root_type_defs, scalars.type_defs, users.type_defs],
        scalars.resolvers + users.resolvers
    )


    # scalars.py
    from ariadne import Scalar
    type_defs = """
        scalar Date
        scalar Datetime
    """

    date = Scalar("Date")
    datetime = Scalar("Datetime")

    # Not shown: scalars implementations

    resolvers = [date, datetime]


    # users.py
    from ariadne import ResolverMap

    type_defs = """
        type User {
            username: String!
            joinedOn: Date!
            lastVisitOn: Datetime
        }
    """

    user = ResolverMap("User)
    # Not shown: user fields resolvers definitions

    # Add users resolver for Query
    query = ResolverMap("Query")

    @query.field("resolve_users")
    def resolve_users(*_):
        return get_some_users()


    resolvers = [user, query]
