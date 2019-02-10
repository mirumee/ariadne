.. _documenting-schema:

Documenting schema
=======================

You can improve the experience of consuming your GraphQL API by documenting the types that it supports.

Keeping your documentation close to the code that supports it is a great way to ensure that it is always accurate and up-to-date. To support this workflow, GraphQL allows programmers to write descriptions directly alongside types in `GraphQL Schema Definition Language syntax <https://facebook.github.io/graphql/June2018/#sec-Descriptions>`_.


Writing Descriptions
--------------------

GraphQL descriptions are declared using a python-like docstring format, and may include Markdown features::

    query = '''
        """
        A simple GraphQL schema which is well described.
        """
        type Query {
            "A list of all users of the service."
            users: [User]!
        }
    '''

    user = '''
        """
        A user is an individual's account.
        """
        type User {
            "Unique ID of the object."
            id: ID!

            "The name the user is identified by in the service."
            username: String!

            "The date this user object was created."
            joinedOn: Datetime!

            "The user's birth data."
            birthDay: Date!
        }
    '''


Introspection
-------------

GraphQL descriptions defined this way will become available via a GraphQL introspection query. This will also permit interactive GraphQL API explorers to include your descriptions in their interactive documentation::

    query IntrospectionQuery {
        __schema {
            types {
                kind
                name
                description
            }
        }
    }

.. code-block:: json

    {
        "__schema": {
            "types": [
                {
                    "kind": "OBJECT",
                    "name": "Query",
                    "description": "A simple GraphQL schema which is well described.",
                }
            ]
        }
    }
