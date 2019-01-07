Ariadne
=======

Ariadne is a Python library for implementing `GraphQL <http://graphql.github.io/>`_ servers.

It presents a simple, easy-to-learn and extend API inspired by `Apollo Server <https://www.apollographql.com/docs/apollo-server/>`_, with a declaratory approach to type definition that uses a standard `Schema Definition Language <https://graphql.github.io/learn/schema/>`_ shared between GraphQL tools, production-ready WSGI middleware, simple dev server for local experiments and an awesome GraphQL Playground for exploring your APIs.


Features
--------

- Simple, quick to learn and easy to memorize API.
- Compatibility with GraphQL.js version 14.0.2.
- Queries, mutations and input types.
- Asynchronous resolvers and query execution.
- Custom scalars and enums.
- Defining schema using SDL strings.
- Loading schema from ``.graphql`` files.
- GraphQL syntax validation and colorization via ``gql()`` helper function.
- WSGI middleware for implementing GraphQL in existing sites.
- Opt-in automatic resolvers mapping between `pascalCase` and ``snake_case``.
- Build-in simple synchronous dev server for quick GraphQL experimentation and GraphQL Playground.
- Support for `Apollo GraphQL extension for Visual Studio Code <https://marketplace.visualstudio.com/items?itemName=apollographql.vscode-apollo>`_.

Following features should work but are not tested and documented: unions, interfaces and subscriptions.


Requirements and installation
-----------------------------

Ariadne requires Python 3.6 or 3.7 and can be installed from Pypi::

    pip install ariadne


Table of contents
-----------------

.. toctree::
   :maxdepth: 2

   introduction
   resolvers
   mutations
   error-messaging
   scalars
   enums
   modularization
   wsgi-middleware
   custom-server
   logo
