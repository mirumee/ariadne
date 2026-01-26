---
id: hiding-field-suggestions
title: Hiding field suggestions
sidebar_label: Hiding field suggestions
---

## Field suggestion

### Description

The introduction of this feature has enabled the correction of typos in GraphQL requests. It can be employed to infer an introspection schema, even when the latter is closed.

It is therefore recommended to always disable field suggestion, particularly when introspection has been disabled on the application.

````graphql
query { me { od } }
````

````json
{
  "error": {
    "errors": [
      {
        "message": "Cannot query field 'od' on type 'User'. Did you mean 'id'?",
        "locations": [
          {
            "line": 3,
            "column": 5
          }
        ],
        "extensions": {
          "exception": null
        }
      }
    ]
  }
}
````

### Disabling field suggestions

The following code presents an error formatter for that will filter out the suggestions.

```python
def hide_field_suggestion_fmt(error: GraphQLError, debug: bool = False) -> dict:
    formatted = error.formatted
    formatted["message"] = re.sub(r"Did you mean.*", "", formatted["message"])
    return formatted

schema = make_executable_schema(type_defs, query)
app = GraphQL(schema, error_formatter=hide_field_suggestion_fmt)
```
