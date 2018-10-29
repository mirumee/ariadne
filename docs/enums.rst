Enums
=====

Ariadne supports Enums, which are represented as strings in Python logic::

    from db import get_users_ids

    type_defs = """
        type Query{
            users(status: UserStatus): [ID!]!
        }

        enum UserStatus{
            ACTIVE
            INACTIVE
            BANNED
        }
    """


    def resolve_users(*_, status):
        if status == "ACTIVE":
            return get_users_ids(is_active=True)
        if status == "INACTIVE":
            return get_users_ids(is_active=False)
        if status == "BANNED":
            return get_users_ids(is_banned=True)
    

    resolvers = {
        "Query": {
            "users": resolve_users,
        }
    }
