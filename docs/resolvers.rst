Resolvers
=========

Intro
-----

In Ariadne, a resolver is any Python callable that accepts two positional arguments (``obj`` and ``info``)::

    def example_resolver(obj: Any, info: ResolveInfo):
        return obj.do_something()


    class FormResolver:
        def __call__(self, obj: Any, info: ResolveInfo, **data):


``obj`` is a value returned by obj resolver. If resolver is *root resolver* (it belongs to the field defined on ``Query`` or ``Mutation``) and GraphQL server implementation doesn't explicitly define value for this field, the value of this argument will be ``None``.

``info`` is the instance of ``ResolveInfo`` object specific for this field and query. It defines a special ``context`` attribute that contains any value that GraphQL server provided for resolvers on the query execution. Its type and contents are application-specific, but it is generally expected to contain application-specific data such as authentication state of the user or http request.

.. note::
   ``context`` is just one of many attributes that can be found on ``ResolveInfo``, but it is by far the most commonly used one. Other attributes enable developers to introspect the query that is currently executed and implement new utilities and abstractions, but documenting that is out of Ariadne's scope. Still, if you are interested, you can find the list of all attributes `here <https://github.com/graphql-python/graphql-core/blob/02605b1adce7b287fa9ee6beacd735882954159a/graphql/execution/base.py#L66>`_.


Handling arguments
------------------

If GraphQL field specifies any arguments, those arguments values will be passed to the resolver as keyword arguments::

    type_def = """
        type Query {
            holidays(year: Int): [String]!
        }
    """ 

    def resolve_holidays(*_, year=None):
        if year:
            Calendar.get_holidays_in_year(year)
        return Calendar.get_all_holidays()

If field argument is marked as required (by following type with ``!``, eg. ``year: Int!``), you can skip the ``=None`` in your kwarg::

    def resolve_holidays(*_, year):
        if year:
            Calendar.get_holidays_in_year(year)
        return Calendar.get_all_holidays()


Default resolver
----------------

In cases when the field has no resolver explicitly provided for it, Ariadne will fall back to the default resolver.

This resolver takes field name and, depending if obj object is ``dict`` or not, uses `get(field_name)` or `getattr(obj, field_name, None)` to resolve the value that should be returned::

    type_def = """
        type User {
            username: String!
        }
    """

    # We don't have to write username resolver
    # for either of those "User" representations:
    class UserObj:
        username = "admin"

    user_dict = {"username": "admin"}

If resolved value is callable, it will be called and its result will be returned to response instead. If field was queried with arguments, those will be passed to the function as keyword arguments, just like how they are passed to regular resolvers::

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


Mapping
-------

Ariadne provides ``resolve_to`` utility function, allowing easy creation of resolvers for fields that are named differently to source attributes (or keys)::

    from ariadne import resolve_to

    # ...type and resolver definitions...

    resolvers = {
        "User": {
            "firstName": resolve_to("first_name"),
            "role": resolve_to("title"),
        }
    }

Resolution logic for ``firstName`` and ``role`` fields will now be identical to the one provided by default resolver described above. The only difference will be that the resolver will look at different names.