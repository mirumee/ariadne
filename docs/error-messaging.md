---
id: error-messaging
title: Error messaging
---


If you've experimented with GraphQL, you should be familiar that when things don't go according to plan, GraphQL servers include an additional key `errors` in the returned response:

```json
{
    "errors": [
        {
            "message": "Variable \"$input\" got invalid value {}.\nIn field \"name\": Expected \"String!\", found null.",
            "locations": [
                {
                    "line": 1,
                    "column": 21
                }
            ]
        }
    ]
}
```

Your first instinct when planning error messaging may be to use this approach to communicate custom errors (like permission or validation errors) raised by your resolvers.

**Don't do this.**

The `errors` key is, by design, supposed to relay errors to other developers working with the API. Messages present under this key are technical in nature and shouldn't be displayed to your end users.

Instead, you should define custom fields that your queries and mutations will include in result sets, to relay eventual errors and problems to clients, like this:

```graphql
type Mutation {
  login(username: String!, password: String!): LoginResult!
}

type LoginResult {
  error: String
  user: User
}
```

Depending on success or failure, your mutation resolver may return either an `error` message to be displayed to the user, or `user` that has been logged in. Your API result-handling logic may then interpret the response based on the content of those two keys, only falling back to the main `errors` key to make sure there wasn't an error in query syntax, connection or application.

Likewise, your `Query` resolvers may return `None` instead of the requested object, which client developers may interpret as a signal from the API to display a "Requested item doesn't exist" message to the user in place of the requested resource.


## Debugging errors

By default individual `errors` elements contain a very limited amount of information about errors occurring inside the resolvers, forcing a developer to search an application's logs for details about the error's possible causes.

Developer experience can be improved by including `debug=True` in the list of arguments passed to Ariadne's `GraphQL` object:

```python
app = GraphQL(schema, debug=True)
```

This will result in each error having an additional `exception` key containing both a complete stacktrace and current context for which the error has occurred:

```json
{
    "errors": [
        {
            "message": "'dict' object has no attribute 'build_name'",
            "locations": [
                [
                    3,
                    5
                ]
            ],
            "path": [
                "people",
                0,
                "fullName"
            ],
            "extensions": {
                "exception": {
                    "stacktrace": [
                        "Traceback (most recent call last):",
                        "  File \"/Users/lib/python3.6/site-packages/graphql/execution/execute.py\", line 619, in resolve_field_value_or_error",
                        "    result = resolve_fn(source, info, **args)",
                        "  File \"myapp.py\", line 40, in resolve_person_fullname",
                        "    return get_person_fullname(person)",
                        "  File \"myapp.py\", line 47, in get_person_fullname",
                        "    return person.build_name()",
                        "AttributeError: 'dict' object has no attribute 'build_name'"
                    ],
                    "context": {
                        "person": "{'firstName': 'John', 'lastName': 'Doe', 'age': 21}"
                    }
                }
            }
        }
    ]
}
```


## Replacing default error formatter

The default error formatter used by Ariadne performs the following tasks:

* Formats error by using its `formatted` property.
* Recursively unwraps the `GraphQL` error by accessing its `original_error` property. 
* If the unwrapped error is available and the `debug` argument is set to `True`, update the already formatted error to also include an `extensions` entry with an `exception` dictionary containing `stacktrace` and `context`.

If you wish to change or customize this behavior, you can define a custom function in the `error_formatter` argument to a `GraphQL` object:

```python
from ariadne import format_error

def my_format_error(error: GraphQLError, debug: bool = False) -> dict:
    if debug:
        # If debug is enabled, reuse Ariadne's formatting logic (not required)
        return format_error(error, debug)

    # Create formatted error data
    formatted = error.formatted
    # Replace original error message with custom one
    formatted["message"] = "INTERNAL SERVER ERROR"
    return formatted

app = GraphQL(schema, error_formatter=my_format_error)
```
