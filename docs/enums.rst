Enumeration types
=================

Ariadne supports `enumeration types <https://graphql.org/learn/schema/#enumeration-types>`_, which are represented as strings in Python logic::

    from db import get_users

    type_defs = """
        type Query{
            users(status: UserStatus): [User]!
        }

        enum UserStatus{
            ACTIVE
            INACTIVE
            BANNED
        }
    """


    def resolve_users(*_, status):
        if status == "ACTIVE":
            return get_users(is_active=True)
        if status == "INACTIVE":
            return get_users(is_active=False)
        if status == "BANNED":
            return get_users(is_banned=True)
    

    resolvers = {
        "Query": {
            "users": resolve_users,
        }
    }

The above example defines a resolver that returns a list of users based on user status, defined using ``UserStatus`` enumerable from schema.

Implementing logic validating if ``status`` value is allowed is not required - this is done on a GraphQL level. This query will produce error::

    {
        users(status: TEST)
    }

GraphQL failed to find ``TEST`` in ``UserStatus``, and returned error without calling ``resolve_users``::

    {
        "error": {
            "errors": [
                {
                    "message": "Argument \"status\" has invalid value TEST.\nExpected type \"UserStatus\", found TEST.",
                    "locations": [
                        {
                            "line": 2,
                            "column": 14
                        }
                    ]
                }
            ]
        }
    }
  