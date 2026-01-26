---
id: disabling-stack-traces
title: Disabling stack traces
sidebar_label: Disabling stack traces
---

## Stack traces

### Description

The Ariadne engine includes a debug mode which attaches stacktraces and error properties to GraphQL requests.

In order to protect against engine targeted attacks and ensure that credentials do not leak in stacktraces, it is essential to disable debug mode in production.

The following presents an error occuring when the server tries to fetch data from the database. This response exposes the **complete database URL.**

```json
{
  "data": {
    "me": null
  },
  "errors": [
    {
      "message": "no such column: \"username\"",
      "locations": [
        {
          "line": 1,
          "column": 16
        }
      ],
      "path": [
        "request0"
      ],
      "extensions": {
        "exception": {
          "stacktrace": [
            "Traceback (most recent call last):",
            "  File \"/root/.cache/pypoetry/virtualenvs/gontoz-9TtSrW0h-py3.11/lib/python3.11/site-packages/graphql/execution/execute.py\", line 528, in await_result",
            "    return_type, field_nodes, info, path, await result",
            "                                          ^^^^^^^^^^^^",
            "  File \"/root/.cache/pypoetry/virtualenvs/gontoz-9TtSrW0h-py3.11/lib/python3.11/site-packages/ariadne/utils.py\", line 70, in async_wrapper",
            "    return await func(*args, **convert_to_snake_case(kwargs))",
            "           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
            "  File \"/app/gontoz/queries.py\", line 100, in resolve_transactions",
            "    return database.get_transaction_from_vuln(",
            "           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",
            "  File \"/app/gontoz/database_manager/main.py\", line 274, in get_transaction_from_vuln",
            "    for transaction in self.cur.execute(query).fetchall():",
            "                       ^^^^^^^^^^^^^^^^^^^^^^^",
            "sqlite3.OperationalError: no such column: None"
          ],
          "context": {
            "self": "<myapp.datab...x7f502112f890>",
            "user_id": "None",
            "query": "'SELECT * FRO...user_to = 125'",
            "transactions": "[]",
            "database_url": "postgresql://user:pass@db:5432/db",
          }
        }
      }
    }
  ]
}
```

### Hiding stack traces

When running an application in production, make sure the debug mode is not enabled.

```python
app = GraphQL(schema, debug=False)
```
