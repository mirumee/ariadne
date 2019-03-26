Local development
=================

Starting a local server
-----------------------

You will need an ASGI server such as `uvicorn <http://www.uvicorn.org/>`_, `daphne <https://github.com/django/daphne/>`_, or `hypercorn <https://pgjones.gitlab.io/hypercorn/>`_::

    $ pip install uvicorn

Pass an instance of ``ariadne.asgi.GraphQL`` to the server to start your API server::

    from ariadne import make_executable_schema
    from ariadne.asgi import GraphQL
    from . import type_defs, resolvers

    schema = make_executable_schema(type_defs, resolvers)
    app = GraphQL(schema)

Run the server pointing it to your file::

    $ uvicorn example:app