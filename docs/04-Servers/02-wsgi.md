---
id: wsgi
title: WSGI application
---


Ariadne provides a `GraphQL` class that implements a production-ready WSGI application.

Ariadne also provides `GraphQLMiddleware` that allows you to route between a `GraphQL` instance and another WSGI app based on the request path.


## Using with a WSGI server

First create an application instance pointing it to the schema to serve:

```python
# in mywsgi.py
import os

from ariadne import make_executable_schema
from ariadne.wsgi import GraphQL
from mygraphql import type_defs, resolvers

schema = make_executable_schema(type_defs, resolvers)
application = GraphQL(schema)
```

Then point a WSGI server such as uWSGI or Gunicorn at the above instance.

Example using Gunicorn:

```console
$ gunicorn mywsgi:application
```

Example using uWSGI:

```console
$ uwsgi --http :8000 --wsgi-file mywsgi
```


### Configuration options

See the [reference](../API-reference/wsgi-reference#constructor).


## Using the middleware

To add GraphQL API to your project using `GraphQLMiddleware`, instantiate it with your existing WSGI application as a first argument and your schema as the second:

```python
# in wsgi.py
import os

from django.core.wsgi import get_wsgi_application
from ariadne import make_executable_schema
from ariadne.wsgi import GraphQL, GraphQLMiddleware
from mygraphql import type_defs, resolvers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mydjangoproject.settings")

schema = make_executable_schema(type_defs, resolvers)
django_application = get_wsgi_application()
graphql_application = GraphQL(schema)
application = GraphQLMiddleware(django_application, graphql_application)
```

Now direct your WSGI server to `wsgi.application`. The GraphQL API is available on `/graphql/` by default but this can be customized by passing a different path as the third argument:

```python
# GraphQL will now be available on "/graphql-v2/" path
application = GraphQLMiddleware(django_application, graphql_application, "/graphql-v2/")
```