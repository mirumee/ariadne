Error messaging
===============

If you've experimented with GraphQL, you should be familiar that when things don't go according to plan, GraphQL servers include additional key ``errors`` to the returned response::

    {
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


Debugging errors
----------------

By default individual ``errors`` elements contain very limited amount of information about errors occurring inside the resolvers, forcing developer to search application's logs for details about possible error's causes.

Developer experience can be improved by including the ``debug=True`` in the list of arguments passed to Ariadne's ``GraphQL`` object::

    app = GraphQL(schema, debug=True)

This will result in each error having additional ``exception`` key containing both complete traceback, and current context for which error has occurred::

    {
        "errors": [
            {
                "message": "'dict' object has no attribute 'build_name'",
                "locations": [
                    [
                        3,
                        5
                    ]
                ],
                "path": [
                    "people",
                    0,
                    "fullName"
                ],
                "extensions": {
                    "exception": {
                        "traceback": [
                            "Traceback (most recent call last):",
                            "  File \"/Users/lib/python3.6/site-packages/graphql/execution/execute.py\", line 619, in resolve_field_value_or_error",
                            "    result = resolve_fn(source, info, **args)",
                            "  File \"myapp.py\", line 40, in resolve_person_fullname",
                            "    return get_person_fullname(person)",
                            "  File \"myapp.py\", line 47, in get_person_fullname",
                            "    return person.build_name()",
                            "AttributeError: 'dict' object has no attribute 'keyz'"
                        ],
                        "context": {
                            "person": "{'firstName': 'John', 'lastName': 'Doe', 'age': 21}"
                        }
                    }
                }
            }
        ]
    }


Replacing default error formatter
---------------------------------

Default error formatter used by Ariadne performs following tasks:

* Formats error by using it's ``formatted`` property.
* Unwraps ``GraphQL`` error by accessing its ``original_error`` property.
* If unwrapped error is available and ``debug`` argument is set to ``True``, update already formatted error to also include ``extensions`` entry with ``exception`` dictionary containing ``traceback`` and ``context``.

If you wish to change or customize this behavior, you can set custom function in ``error_formatter`` of ``GraphQL`` object::

    from ariadne import format_error

    def my_format_error(error: GraphQLError, debug: bool = False) -> dict:
        if debug:
            # If debug is enabled, reuse Ariadne's formatting logic (not required)
            return format_error(error, debug)

        # Create formatted error data
        formatted = error.formatted
        # Replace original error message with custom one
        formatted["message"] = "INTERNAL SERVER ERROR"
        return formatted

    app = GraphQL(schema, error_formatter=my_format_error)