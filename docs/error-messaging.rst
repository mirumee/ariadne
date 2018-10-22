Error messaging
===============

If you've experimented with GraphQL, you should be familiar that when things don't go according to plan, GraphQL servers include additional key ``errors`` to returned response::

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

The ``errors`` key is, by design, supposed to relay errors to other developers working with the API. Messages present under this key are technical and are not supposed to be displayed to your application users.

Instead, you should define custom fields that your queries and mutations will include in result sets to rely eventual errors and problems to clients, like this::

    type_def = """
        type Mutation {
            login(username: String!, password: String!) {
                error: String
                user: User
            }
        }
    """

Depending on success or failure, your mutation resolver may return either ``error`` message to be displayed to user, or ``user`` that has been logged in. Your API result handling logic may then interpret the response based on content of those two keys, only falling back to main ``errors`` key to make sure there wasn't error in query syntax, connection or application.