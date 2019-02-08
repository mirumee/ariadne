Union types
===========

When designing your API you may run into a situation where you want your field to resolve to one of few possible types. It may be an ``error`` field that can resolve to one of many error types, or an activity feed made of different types.

Most obvious solution may be creating custom "intermediary" type that would define dedicated fields to different types::

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

GraphQL provides dedicated solution to this problem in the form of dedicated `Union` type.


Union example
-------------

Consider earlier error example. Union representing one of possible three error types can be defined in schema like this::

    union Error = NotFoundError | AccessError | ValidationError

This ``Error`` type can be used just like any other type::

    type MutationPayload {
        status: Boolean!
        error: Error
        user: User
    }

Your union will also need a special resolver named *type resolver*. This resolver will we called with an object returned from field resolver and current context, and should return string containing name of an GraphQL type, or ``None`` if received type is incorrect::

    def resolve_error_type(obj, *_):
        if isinstance(obj, ValidationError):
            return "ValidationError"
        if isinstance(obj, AccessError):
            return "AccessError"
        return None

.. note::
   Returning ``None`` from this resolver will result in ``null`` being returned for this field in your query's result.

Ariadne provides special ``Union`` class that allows you to bind this function to Union in your schema::

    from ariadne import Union

    error = Union("Error")

    @error.type_resolver
    def resolve_error_type(obj, *_):
        ...

If this function is already defined elsewhere (eg. 3rd party package), you can instantiate the ``Union`` with it as second argument::

    from ariadne import Union
    from .graphql import resolve_error_type

    error = Union("Error", resolve_error_type)

Lastly, your ``Union`` instance should be passed to ``make_executable_schema`` together will other resolvers::

    schema = make_executable_schema(type_defs, [query, error])


``__typename`` field
--------------------

Every type in GraphQL has special ``__typename`` field that is resolved to string containing type's name.

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

Assuming that feed is a list, query could produce following response::

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