.. _unions:

Union types
===========

When designing your API, you may run into a situation where you want your field to resolve to one of a few possible types. It may be an ``error`` field that can resolve to one of many error types, or an activity feed made up of different types.

The most obvious solution may be creating a custom "intermediary" type that would define dedicated fields to different types::

    type MutationPayload {
        status: Boolean!
        validationError: ValidationError
        permissionError: AccessError
        user: User
    }

    type FeedItem {
        post: Post
        image: Image
        user: User
    }

GraphQL provides a dedicated solution to this problem in the form of dedicated ``Union`` type.


Union example
-------------

Consider an earlier error example. The union representing one of a possible three error types can be defined in schema like this::

    union Error = NotFoundError | AccessError | ValidationError

This ``Error`` type can be used just like any other type::

    type MutationPayload {
        status: Boolean!
        error: Error
        user: User
    }

Your union will also need a special resolver named *type resolver*. This resolver will we called with an object returned from a field resolver and current context, and should return a string containing the name of an GraphQL type, or ``None`` if received type is incorrect::

    def resolve_error_type(obj, *_):
        if isinstance(obj, ValidationError):
            return "ValidationError"
        if isinstance(obj, AccessError):
            return "AccessError"
        return None

.. note::
   Returning ``None`` from this resolver will result in ``null`` being returned for this field in your query's result. If field is not nullable, this will cause the GraphQL query to error.

Ariadne relies on dedicated ``UnionType`` class for bindinding this function to Union in your schema::

    from ariadne import UnionType

    error = UnionType("Error")

    @error.type_resolver
    def resolve_error_type(obj, *_):
        ...

If this function is already defined elsewhere (e.g. 3rd party package), you can instantiate the ``UnionType`` with it as second argument::

    from ariadne import UnionType
    from .graphql import resolve_error_type

    error = UnionType("Error", resolve_error_type)

Lastly, your ``UnionType`` instance should be passed to ``make_executable_schema`` together will other types::

    schema = make_executable_schema(type_defs, [query, error])


``__typename`` field
--------------------

Every type in GraphQL has a special ``__typename`` field that is resolved to a string containing the type's name.

Including this field in your query may simplify implementation of result handling logic in your client::

    query getFeed {
        feed {
            __typename
            ... on Post {
                text
            }
            ... on Image {
                url
            }
            ... on User {
                username
            }
        }
    }

Assuming that the feed is a list, the query could produce the following response::

    {
        "data": {
            "feed": [
                {
                    "__typename": "User",
                    "username": "Bob"
                },
                {
                    "__typename": "User",
                    "username": "Aerith"
                },
                {
                    "__typename": "Image",
                    "url": "http://placekitten.com/200/300"
                },
                {
                    "__typename": "Post",
                    "text": "Hello world!"
                },
                {
                    "__typename": "Image",
                    "url": "http://placekitten.com/200/300"
                }
            ]
        }
    }

Client code could check the ``__typename`` value of every item in the feed to decide how it should be displayed in the interface.