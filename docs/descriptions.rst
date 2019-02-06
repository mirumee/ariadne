.. _descriptions:

Descriptions
============

Ariadne supports Descriptions via `GraphQL Schema Definition Language syntax <https://facebook.github.io/graphql/June2018/#sec-Descriptions>`_.


Declaration
-----------

GraphQL Descriptions are declared using a python-like docstring format, and may include Markdown features::

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

GraphQL Descriptions defined this way will become available via a GraphQL introspection query.  This will also permit interactive GraphQL API explorers to include your descriptions in their interactive documentation::

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
