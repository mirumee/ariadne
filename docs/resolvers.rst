.. _resolvers:

Resolvers
=========

Intro
-----

In Ariadne, a resolver is any Python callable that accepts two positional arguments (``obj`` and ``info``)::

    def example_resolver(obj: Any, info: GraphQLResolveInfo):
        return obj.do_something()

    class FormResolver:
        def __call__(self, obj: Any, info: GraphQLResolveInfo, **data):


``obj`` is a value returned by an obj resolver. If the resolver is a *root resolver* (it belongs to the field defined on ``Query`` or ``Mutation``) and GraphQL server implementation doesn't explicitly define value for this field, the value of this argument will be ``None``.

``info`` is the instance of a ``GraphQLResolveInfo`` object specific for this field and query. It defines a special ``context`` attribute that contains any value that GraphQL server provided for resolvers on the query execution. Its type and contents are application-specific, but it is generally expected to contain application-specific data such as authentication state of the user or http request.

.. note::
   ``context`` is just one of many attributes that can be found on ``GraphQLResolveInfo``, but it is by far the most commonly used one. Other attributes enable developers to introspect the query that is currently executed and implement new utilities and abstractions, but documenting that is out of Ariadne's scope. If you are interested, you can find the list of all attributes `here <https://github.com/graphql-python/graphql-core-next/blob/d24f556c20282993d52ccf7a7cf36bacec5ed7db/graphql/type/definition.py#L446>`_.


Resolver maps
-------------

A resolver needs to be bound to a valid type's field in the schema in order to be used during the query execution.

To bind resolvers to schema, Ariadne uses a special ``ResolverMap`` object that is initialized with single argument - name of the type::

    from ariadne import ResolverMap

    query = ResolverMap("Query")

The above ``ResolverMap`` instance knows that it maps its resolvers to ``Query`` type, and enables you to assign resolver functions to these type fields. This can be done using the ``field`` method implemented by the resolver map::

    from ariadne import ResolverMap

    type_defs = """
        type Query {
            hello: String!
        }
    """

    query = ResolverMap("Query")

    @query.field("hello")
    def resolve_hello(*_):
        return "Hello!"

``@query.field`` decorator is non-wrapping - it simply registers a given function as a resolver for specified field and then returns it as it is. This makes it easy to test or reuse resolver functions between different types or even APIs::

    user = ResolverMap("User")
    client = ResolverMap("Client")

    @user.field("email")
    @client.field("email")
    def resolve_email_with_permission_check(obj, info):
        if info.context.user.is_administrator:
            return obj.email
        return None

Alternatively, ``query.field`` can also be called as regular method::

    from .resolvers import resolve_email_with_permission_check

    user = ResolverMap("User")
    user.field("email", resolver=resolve_email_with_permission_check)


Handling arguments
------------------

If GraphQL field specifies any arguments, those argument values will be passed to the resolver as keyword arguments::

    type_def = """
        type Query {
            holidays(year: Int): [String]!
        }
    """

    user = ResolverMap("Query")

    @query.field("holidays")
    def resolve_holidays(*_, year=None):
        if year:
            Calendar.get_holidays_in_year(year)
        return Calendar.get_all_holidays()

If a field argument is marked as required (by following type with ``!``, eg. ``year: Int!``), you can skip the ``=None`` in your ``kwarg``::

    @query.field("holidays")
    def resolve_holidays(*_, year):
        if year:
            Calendar.get_holidays_in_year(year)
        return Calendar.get_all_holidays()


Aliases
-------

You can use ``ResolverMap.alias`` to quickly make a field an alias for a differently-named attribute on a resolved object::

    type_def = """
        type User {
            fullName: String
        }
    """ 

    user = ResolverMap("User")
    user.alias("fullName", "username")


Fallback resolvers
------------------

Schema can potentially define numerous types and fields, and defining a resolver or alias for every single one of them can become a large burden.

Ariadne provides two special "fallback resolvers" that scan schema during initialization, and bind default resolvers to fields that don't have any resolver set::

    from ariadne import fallback_resolvers, make_executable_schema
    from .typedefs import type_defs
    from .resolvers import resolvers

    schema = make_executable_schema(type_defs, resolvers + [fallback_resolvers])

The above example starts a simple GraphQL API using types and resolvers imported from other modules, but it also adds ``fallback_resolvers`` to the list of resolvers that should be used in creation of schema. 

``fallback_resolvers`` perform any case conversion and simply seek the attribute named in the same way as the field they are bound to using "default resolver" strategy described in the next chapter.

If your schema uses JavaScript convention for naming its fields (as do all schema definitions in this guide) you may want to instead use the ``snake_case_fallback_resolvers`` that converts field name to Python's ``snake_case`` before looking it up on the object::

    from ariadne import snake_case_fallback_resolvers, make_executable_schema
    from .typedefs import type_defs
    from .resolvers import resolvers

    schema = make_executable_schema(type_defs, resolvers + [snake_case_fallback_resolvers])


Default resolver
----------------

Both ``ResolverMap.alias`` and fallback resolvers use an Ariadne-provided default resolver to implement its functionality.

This resolver takes a target attribute name and (depending if ``obj`` is ``dict`` or not) uses either ``obj.get(attr_name)`` or ``getattr(obj, attr_name, None)`` to resolve the value that should be returned.

In the below example, both representations of ``User`` type are supported by the default resolver::

    type_def = """
        type User {
            likes: Int!
            initials(length: Int!): String
        }
    """

    class UserObj:
        username = "admin"

        def likes(self):
            return count_user_likes(self)

        def initials(self, length)
            return self.name[:length]

    user_dict = {
        "likes": lambda obj, *_: count_user_likes(obj),
        "initials": lambda obj, *_, length: obj.username[:length])
    }


Understanding schema binding
----------------------------

When Ariadne initializes GraphQL server, it iterates over a list of objects passed to a ``resolvers`` argument and calls ``bind_to_schema`` method of each item with a single argument: instance of ``GraphQLSchema`` object representing parsed schema used by the server.

``ResolverMap`` and the fallback resolvers introduced above don't access the schema until their ``bind_to_schema`` method is called. It is safe to create, call methods and perform other state mutations on those objects until they are passed to Ariadne.

You can easily implement a custom utility class that can be used in Ariadne::

    from graphql.type import GraphQLSchema

    class MyResolverMap:
        def bind_to_schema(self, schema: GraphQLSchema) -> None:
            pass  # insert custom logic here

In later parts of the documentation, other special types will be introduced that internally use ``bind_to_schema`` to implement their logic.
