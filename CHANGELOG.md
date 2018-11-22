# CHANGELOG

## 0.2.0 (UNRELEASED)

- Removed support for Python 3.5 and added support for 3.7.
- Moved to `GraphQL-core-next` that supports `async` resolvers, query execution and implements more recent version of GraphQL spec. If you are updating existing project, you will need to uninstall `graphql-core` before installing `graphql-core-next`, as both libraries use `graphql` namespace.
- Added `gql()` utility that provides GraphQL string validation on declaration time, and enables use of [Apollo-GraphQL](https://marketplace.visualstudio.com/items?itemName=apollographql.vscode-apollo) plugin in Python code.
- Added `start_simple_server()` shortcut for creating simple server with `GraphQLMiddleware.make_server()` and then running it with `serve_forever()`.
- `Boolean` built-in scalar now checks the type of each serialized value. Returning values of type other than `bool`, `int` or `float` from a field resolver will result in a `Boolean cannot represent a non boolean value` error.
- Redefining type in `type_defs` will now result in `TypeError` being raised. This is breaking change from previous behaviour where old type was simply replaced with new one.
- Returning `None` from scalar `parse_literal` and `parse_value` function no longer results in GraphQL API producing default error message. Instead `None` will be passed further down to resolver or producing "value is required" error if its marked as such with `!` For old behaviour raise either `ValueError` or `TypeError`. See documentation for more details.