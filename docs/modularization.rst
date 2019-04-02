Modularization
==============

Ariadne allows you to spread your GraphQL API implementation over multiple files, with different strategies being available for schema and resolvers.


Defining schema in ``.graphql`` files
-------------------------------------

Recommended way to define schema is by using the ``.graphql`` files. This approach offers certain advantages:

- First class support from developer tools like `Apollo GraphQL plugin <https://marketplace.visualstudio.com/items?itemName=apollographql.vscode-apollo>`_ for VS Code.
- Easier cooperation and sharing of schema design between frontend and backend developers.
- Dropping whatever python boilerplate code was used for SDL strings.

To load schema from file or directory, you can use the ``load_schema_from_path`` utility provided by the Ariadne::

    from ariadne import load_schema_from_path
    from ariadne.asgi import GraphQL

    # Load schema from file...
    type_defs = load_schema_from_path("/path/to/schema.graphql")

    # ...or construct schema from all *.graphql files in directory
    type_defs = load_schema_from_path("/path/to/schema/")

    # Build an executable schema
    schema = make_executable_schema(type_defs)

    # Create an ASGI app for the schema
    app = GraphQL(schema)

The above app won't be able to execute any queries but it will allow you to browse your schema.

``load_schema_from_path`` validates syntax of every loaded file, and will raise an ``ariadne.exceptions.GraphQLFileSyntaxError`` if file syntax is found to be invalid.


Defining schema in multiple modules
-----------------------------------

Because Ariadne expects ``type_defs`` to be either string or list of strings, it's easy to split types across many string variables in many modules::

    query = """
        type Query {
            users: [User]!
        }
    """

    user = """
        type User {
            id: ID!
            username: String!
            joinedOn: Datetime!
            birthDay: Date!
        }
    """

    scalars = """
        scalar Datetime
        scalar Date
    """

    schema = make_executable_schema([query, user, scalars])

The order in which types are defined or passed to ``type_defs`` doesn't matter, even if those types depend on each other.


Defining types in multiple modules
----------------------------------

Just like ``type_defs`` can be a string or list of strings, ``bindables`` can be a single instance, or a list of instances::

    schema = ... # valid schema definition

    from .types import query, user
    from .scalars import scalars

    resolvers = [query, user]
    resolvers += scalars  # [date_scalar, datetime_scalar]

    schema = make_executable_schema(schema, resolvers)

The order in which objects are passed to the ``bindables`` argument matters. Most bindables replace previously set resolvers with new ones, when more than one is defined for the same GraphQL type, with ``InterfaceType`` and fallback resolvers being exceptions to this rule.
