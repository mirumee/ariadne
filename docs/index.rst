Ariadne
=======

Ariadne is a Python library for implementing `GraphQL <http://graphql.github.io/>`_ servers.

It exposes simple, easy to learn and extend API inspired by `Apollo Server <https://www.apollographql.com/docs/apollo-server/>`_, declaratory approach to types definition that uses standard `Schema Definition Language <https://graphql.github.io/learn/schema/>`_ shared between GraphQL tools, production-ready WSGI middleware, simple dev server for local experiments and awesome GraphQL Playground for exploring your APIs.

.. note::
   While most of GraphQL standard is already supported, Ariadne is currently missing support for following features: unions, interfaces and inheritance, subscriptions.


Requirements and installation
-----------------------------

Ariadne requires Python 3.5 or 3.6 and can be installed from Pypi::

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
   wsgi-middleware
   custom-server
