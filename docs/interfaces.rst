Interface types
===============

Interface is an abstract GraphQL type that defines certain set of fields and requires other types *implementing* it to also define same fields in order for schema to be correct.


Interface example
-----------------

Consider an application implementing a search function. Search can return items of different type, like ``Client``, ``Order`` or ``Product``. For each result it displays a short summary text that is a link leading to a page containing the item's details.

An ``Interface`` can be defined in schema that forces those types to define the ``summary`` and ``url`` fields::

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


GraphQL standard requires that every type implementing the ``Interface`` also explicitly defines fields from the interface. This is why the ``summary`` and ``url`` fields repeat on all types in the example.

Like with the union, the ``SearchResult`` interface will also need a special resolver named *type resolver*. This resolver will we called with an object returned from a field resolver and current context, and should return a string containing the name of a GraphQL type, or ``None`` if the received type is incorrect::

    def resolve_search_result_type(obj, *_):
        if isinstance(obj, Client):
            return "Client"
        if isinstance(obj, Order):
            return "Order"
        if isinstance(obj, Product):
            return "Product"
        return None

.. note::
   Returning ``None`` from this resolver will result in ``null`` being returned for this field in your query's result. If a field is not nullable, this will cause the GraphQL query to error.

Ariadne relies on a dedicated ``InterfaceType`` class for binding this function to the ``Interface`` in your schema::

    from ariadne import InterfaceType

    search_result = InterfaceType("SearchResult")

    @search_result.type_resolver
    def resolve_search_result_type(obj, *_):
        ...

If this function is already defined elsewhere (e.g. 3rd party package), you can instantiate the ``InterfaceType`` with it as a second argument::

    from ariadne import InterfaceType
    from .graphql import resolve_search_result_type

    search_result = InterfaceType("SearchResult", resolve_search_result_type)

Lastly, your ``InterfaceType`` instance should be passed to ``make_executable_schema`` together with other types::

    schema = make_executable_schema(type_defs, [query, search_result])


Field resolvers
---------------

Ariadne's ``InterfaceType`` instances can optionally be used to set resolvers on implementing types fields.

``SearchResult`` interface from previous section implements two fields: ``summary`` and ``url``. If resolver implementation for those fields is same for multiple types implementing the interface, ``InterfaceType`` instance can be used to set those resolvers for those fields::

    @search_result.field("summary")
    def resolve_summary(obj, *_):
        return str(obj)

    
    @search_result.field("url")
    def resolve_url(obj, *_):
        return obj.get_absolute_url()

``InterfaceType`` extends the :ref:`ObjectType <resolvers>`, so ``set_field` and ``set_alias`` are also available::

    search_result.set_field("summary", resolve_summary)
    search_result.alias("url", "absolute_url")

.. note::
   ``InterfaceType`` assigns the resolver to a field only if that field has no resolver already set. This is different from ``ObjectType`` that sets resolvers fields if field already has other resolver set.
