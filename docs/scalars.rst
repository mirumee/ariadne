Custom scalars
==============

Custom scalars allow you to convert your Python objects to JSON-serializable form in query results, as well as convert those JSON forms back to Python objects back when they are passed as arguments or ``input`` values.


Example read-only scalar
------------------------

Consider this API defining ``Story`` type with ``publishedOn``::

    type_defs = """
        type Story {
            content: String
            publishedOn: String
        }
    """

The ``publishedOn`` field's resolver returns instance of type ``datetime``, but in API this field is defined as ``String``. This means that our datetime will be passed throught the ``str()`` before being returned to client::

    {
        "publishedOn": "2018-10-26 17:28:54.416434"
    }

This may look acceptable, but there are better formats to serialize timestamps for later deserialization on the client, like ISO 8601. We could perform this conversion in our resolver::

    def resolve_published_on(obj, *_):
        return obj.published_on.isoformat()

...but now you will have to remember to define custom resolver for every field that receives ``datetime`` as value. This really adds up the boilerplate to our API, and makes it harder to use abstractions auto-generating the resolvers for you.

Instead, you could tell GraphQL how to serialize dates by defining custom scalar type::

    type_defs = """
        type Story {
            content: String
            publishedOn: Datetime
        }

        scalar Datetime
    """

If you will try to query this field now, you will get error::

    {
        "errors": [
            {
                "message": "Expected a value of type \"Datetime\" but received: 2018-10-26 17:39:55.502078",
                "path": [
                    "publishedOn"
                ]
            }
        ],
    }

This is because our custom scalar has been defined, but it's currently missing logic for serializing Python values to JSON form.

We need to add special resolver named ``serialize`` to our ``Datetime`` scalar that will implement the logic we are expecting::

    def serialize_datetime(value):
        return value.isoformat()

    
    resolvers = {
        "Datetime": {
            "serialize": serialize_datetime
        }
    }

Doing so will make GraphQL server use custom logic whenever value that is not ``None`` is returned from resolver::

    {
        "publishedOn": "2018-10-26T17:45:08.805278"
    }

Now we can reuse our custom scalar across the API to serialize ``datetime`` instances in standardized format that our clients will understand.


Scalars as input
----------------

What will happen if now we create field or mutation that defines argument of the type ``Datetime``? We can find out using basic resolver::

    type_defs = """
        type Query {
            stories(publishedOn: Datetime): [Story!]!
        }
    """

    def resolve_stories(*_, **data):
        print(data.get("publishedOn"))  # what value will "publishedOn" be?

``data.get("publishedOn")`` will return ``False``, because that is fallback value of *read-only* scalars.

To turn our *read-only* scalar into *bidirectional* scalar, we will need to add two functions to ``serialize`` that was implemented in previous step:

- ``parse_value(value)`` that will be used when scalar value is passed as part of query ``variables``.
- ``parse_literal(ast)`` that will be used when scalar value is passed as part of query content (eg. ``{ stories(publishedOn: "2018-10-26T17:45:08.805278") { ... } }``).

Those functions can be implemented as such::

    def parse_datetime_value(value):
        try:
            # dateutil is provided by python-dateutil library
            return dateutil.parser.parse(value)
        except (ValueError, TypeError):
            return None

        
    def parse_datetime_literal(ast):
        value = str(ast.value)
        return parse_value(value)  # reuse logic from parse_value


    resolvers = {
        "Datetime": {
            "serialize": serialize_datetime,
            "parse_value": parse_datetime_value,
            "parse_literal": parse_datetime_literal,
        }
    }

There's few things happening in above code, so let's go through them step by step:

There aren't any checks to see if arguments passed to function are ``None`` because if that is the case, GraphQL server skips our parsing step altogether.

When value is incorrect and either  ``ValueError`` and ``TypeError`` exceptions are raised, they are silenced and function returns ``None`` instead. GraphQL server interprets this as sign that entered value is incorrect because it can't be transformed to internal representation, and returns appropriate error to the client. This is preferable approach to raising exceptions from parser, because in such case those exceptions interrupt query execution logic (prohibiting possible partial result), as well as result in error messages possibly **leaking implementation details** to the client.

If value is passed as part of query content, it's ``ast`` node is instead passed to ``parse_datetime_literal`` to give it chance to introspect type of node (implementations for those be found `here <https://github.com/graphql-python/graphql-core/blob/master/graphql/language/ast.py#L483>`_), but we are opting in for just extracting whatever value this `ast` node had, coercing it to ``str`` and reusing ``parse_value``.