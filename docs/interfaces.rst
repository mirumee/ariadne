Interface types
===============

Just like previously described :ref:`unions <unions>`, interfaces enable you to create fields that resolve to value that is one of few possible types.

Main feature that differs ``Interface`` from the ``Union`` is a contract defined by Schema's creator that GraphQL requires all possible types to implement.

.. note::
   It's recommended that you've read the :ref:`unions` section before continuing.


Interface example
-----------------

Consider an application implementing a search function. This search can return items of different type, like ``Client``, ``Order`` or ``Product``. For each result it displays short summary text that is a link leading to page containing item's details.

An ``Interface`` can be created in schema that enforces that those types define ``summary`` and ``url`` fields::

    interface SearchResult {
        summary: String!
        url: String!
    }

Type definitions can then be updated to ``implement`` this interface::

    type Client implements SearchResult {
        first_name: String!
        last_name: String!
        summary: String!
        url: String!
    }

    type Order implements SearchResult {
        ref: String!
        client: Client!
        summary: String!
        url: String!
    }

    type Product implements SearchResult {
        name: String!
        sku: String!
        summary: String!
        url: String!
    }


GraphQL standard requires that every type implementing the ``Interface`` also explicitly defines the fields that this interface defines. This is why ``summary`` and ``url`` fields repeat on all types in the example.

Like with the union, the ``SearchResult`` interface will also need a special resolver named *type resolver*. This resolver will we called with an object returned from a field resolver and current context, and should return a string containing the name of an GraphQL type, or ``None`` if received type is incorrect::

    def resolve_search_result_type(obj, *_):
        if isinstance(obj, Client):
            return "Client"
        if isinstance(obj, Order):
            return "Order"
        if isinstance(obj, Product):
            return "Product"
        return None

.. note::
   Returning ``None`` from this resolver will result in ``null`` being returned for this field in your query's result. If field is not nullable, this will cause the GraphQL query to error.

Ariadne relies on dedicated ``Interface`` object for bindinding this function to Interface in your schema::

    from ariadne import Interface

    search_result = Interface("SearchResult")

    @search_result.type_resolver
    def resolve_search_result_type(obj, *_):
        ...

If this function is already defined elsewhere (e.g. 3rd party package), you can instantiate the ``Interface`` with it as second argument::

    from ariadne import Interface
    from .graphql import resolve_search_result_type

    search_result = Interface("SearchResult", resolve_search_result_type)

Lastly, your ``Interface`` instance should be passed to ``make_executable_schema`` together will other resolvers::

    schema = make_executable_schema(type_defs, [query, search_result])


Sharing resolvers between types
-------------------------------

Ariadne's ``Interface`` instances can also optionally be used to share resolvers between implementing types::

    @search_result.field("summary")
    def resolve_summary(obj, *_):
        return str(obj)

    
    @search_result.field("url")
    def resolve_url(obj, *_):
        return obj.get_absolute_url()

Like in the :ref:`ResolverMap <resolvers>`, ``field`` can be used as regular method::

    search_result.field("summary", resolver=resolve_summary)
    search_result.field("url", resolver=resolve_url)

Unlike the ``ResolverMap``, ``Interface`` assigns the resolver to field only if that field has no resolver already set.
