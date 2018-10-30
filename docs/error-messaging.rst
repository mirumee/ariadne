Error messaging
===============

If you've experimented with GraphQL, you should be familiar that when things don't go according to plan, GraphQL servers include additional key ``errors`` to the returned response::

    {
        "error": {
            "errors": [
                {
                    "message": "Variable \"$input\" got invalid value {}.\nIn field \"name\": Expected \"String!\", found null.",
                    "locations": [
                        {
                            "line": 1,
                            "column": 21
                        }
                    ]
                }
            ]
        }
    }

Your first instinct when planning error messaging may be to use this approach to communicate custom errors (like permission or validation errors) raised by your resolvers.

**Don't do this.**

The ``errors`` key is, by design, supposed to relay errors to other developers working with the API. Messages present under this key are technical in nature and shouldn't be displayed to your end users.

Instead, you should define custom fields that your queries and mutations will include in result sets, to relay eventual errors and problems to clients, like this::

    type_def = """
        type Mutation {
            login(username: String!, password: String!) {
                error: String
                user: User
            }
        }
    """

Depending on success or failure, your mutation resolver may return either an ``error`` message to be displayed to the user, or ``user`` that has been logged in. Your API result handling logic may then interpret the response based on the content of those two keys, only falling back to the main ``errors`` key to make sure there wasn't an error in query syntax, connection or application.

Likewise, your ``Query`` resolvers may return a requested object or ``None`` that will then cause a message such as "Requested item doesn't exist or you don't have permission to see it" to be displayed to the user in place of the requested resource.