Custom scalars
==============

Custom scalars allow you to convert your Python objects to JSON-serializable form in query results, as well as convert those JSON forms back to Python objects back when they are passed as arguments or ``input`` values.


Example read-only scalar
------------------------

Consider this API defining ``Story`` type with ``publishedOn`` field::

    type_defs = """
        type Story {
            content: String
            publishedOn: String
        }
    """

The ``publishedOn`` field resolver returns instance of type ``datetime``, but in API this field is defined as ``String``. This means that our datetime will be passed throught the ``str()`` before being returned to client::

    {
        "publishedOn": "2018-10-26 17:28:54.416434"
    }

This may look acceptable, but there are better formats to serialize timestamps for later deserialization on the client, like ISO 8601. This conversion could be performed in dedicated resolver::

    def resolve_published_on(obj, *_):
        return obj.published_on.isoformat()

...but now the developer has to remember to define custom resolver for every field that returns ``datetime``. This really adds up the boilerplate to the API, and makes it harder to use abstractions auto-generating the resolvers for you.

Instead, GraphQL API can be told how to serialize dates by defining custom scalar type::

    type_defs = """
        type Story {
            content: String
            publishedOn: Datetime
        }

        scalar Datetime
    """

If you will try to query this field now, you will get an error::

    {
        "error": "Unexpected token A in JSON at position 0"
    }

This is because custom scalar has been defined, but it's currently missing logic for serializing Python values to JSON form and ``Datetime`` instances are not JSON serializable by default.

We need to add special serializing resolver to our ``Datetime`` scalar that will implement the logic we are expecting. Ariadne provides ``Scalar`` class that enables just that::

    from ariadne import Scalar

    datetime_scalar = Scalar("Datetime")

    @datetime_scalar.serializer
    def serialize_datetime(value):
        return value.isoformat()

Include the ``datetime_scalar`` in the list of ``resolvers`` passed to your GraphQL server. Custom serialization logic will now be used when resolver for ``Datetime`` field returns value other than ``None``::

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

``data.get("publishedOn")`` will print ``str`` containing whatever value was passed to the argument. For some scalars this may do the trick, but for this one it's expected that input gets converted back to the ``datetime`` instance.

To turn our *read-only* scalar into *bidirectional* scalar, we will need to add two functions to ``Scalar`` that was created in previous step:

- ``value_parser(value)`` that will be used when scalar value is passed as part of query ``variables``.
- ``literal_parser(ast)`` that will be used when scalar value is passed as part of query content (eg. ``{ stories(publishedOn: "2018-10-26T17:45:08.805278") { ... } }``).

Those functions can be implemented as such::

    @datetime_scalar.value_parser
    def parse_datetime_value(value):
        # dateutil is provided by python-dateutil library
        if value:
            return dateutil.parser.parse(value)

    @datetime_scalar.literal_parser
    def parse_datetime_literal(ast):
        value = str(ast.value)
        return parse_datetime_value(value)  # reuse logic from parse_value

There are few things happening in the above code, so let's go through it step by step:

If value is passed as part of query's ``variables``, it's passed to ``parse_datetime_value``.

If value is not empty, ``dateutil.parser.parse`` is used to parses it to the valid Python ``datetime`` object instance that is then returned.

If value is incorrect and either ``ValueError`` or ``TypeError`` exception is raised by the ``dateutil.parser.parse`` GraphQL server interprets this as sign that entered value is incorrect because it can't be transformed to internal representation and returns automatically generated error message to the client that consists of two parts:

- Part supplied by GraphQL, for example: ``Expected type Datetime!, found "invalid string"``
- Exception message: ``time data 'invalid string' does not match format '%Y-%m-%d'``

Complete error message returned by the API will look like this:: 

    Expected type Datetime!, found "invalid string"; time data 'invalid string' does not match format '%Y-%m-%d'

.. note::
   You can raise either ``ValueError`` or ``TypeError`` in your parsers.
   
.. warning::
   Because error message returned by the GraphQL includes original exception message from your Python code, it may contain details specific to your system or implementation that you may not want to make known to the API consumers. You may decide to catch the original exception with ``except (ValueError, TypeError)`` and then raise your own ``ValueError`` with custom message or no message at all to prevent this from happening.

If value is specified as part of query content, it's ``ast`` node is instead passed to ``parse_datetime_literal`` to give Scalar a chance to introspect type of the node (implementations for those be found `here <https://github.com/graphql-python/graphql-core-next/blob/master/graphql/language/ast.py#L261>`_).

Logic implemented in the ``parse_datetime_literal`` may be completely different from one in the ``parse_datetime_value``, however, in this example ``ast`` node is simply unpacked, coerced to ``str`` and then passed to ``parse_datetime_value``, reusing the parsing logic from that other function.