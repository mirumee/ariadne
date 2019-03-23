.. _documenting-schema:

Documenting schema
==================

You can improve the experience of consuming your GraphQL API by documenting the types that it supports.

Ariadne recommends writing documentation via the `description feature <https://facebook.github.io/graphql/June2018/#sec-Descriptions>`_ in GraphQL Schema Definition Language.  Keeping your documentation close to the code that supports it is a great way to ensure that it is always accurate and up-to-date.


Descriptions
------------

GraphQL descriptions are declared using a docstring format that feels very similar to Python's::

    query = '''
        """
        Search results must always include a summary and a URL for the resource.
        """
        interface SearchResult {
            "A brief summary of the search result."
            summary: String!

            "The URL for the resource the search result is describing."
            url: String!
        }
    '''

Note that GraphQL descriptions also support Markdown (as specified in `CommonMark <https://commonmark.org/>`_)::

    query = '''
        """
        Search results **must** always include a summary and a
        [URL](https://en.wikipedia.org/wiki/URL) for the resource.
        """
        interface SearchResult {
            # ...
        }
    '''


Browsing documentation
----------------------

The most common way you and your users will encounter GraphQL documentation is via an interactive GraphQL API explorer.

In `GraphQL Playground <https://github.com/prisma/graphql-playground>`_ (shipped with Ariadne's startSimpleServer helper), descriptions are available via a documentation browser.

.. image:: _static/graphql-playground-example.jpg
   :alt: GraphQL Playground example


Introspection
-------------

GraphQL descriptions can also be accessed programatically.  Internally, this is how tools like GraphQL Playground can provide the live, dynamic experience they do.

You can get programatic access to a graphQL server's schema using an `introspection query <https://graphql.org/learn/introspection/>`_.  An introspection query is specified using a special field in the Query type, using standard GraphQL query syntax::

    query IntrospectionQuery {
        __schema {
            types {
                kind
                name
                description
            }
        }
    }

A response to the above query might look like this:

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
