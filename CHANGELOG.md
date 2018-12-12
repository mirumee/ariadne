# CHANGELOG

## 0.2.0 (UNRELEASED)

- Removed support for Python 3.5 and added support for 3.7.
- Moved to `GraphQL-core-next` that supports `async` resolvers, query execution and implements more recent version of GraphQL spec. If you are updating existing project, you will need to uninstall `graphql-core` before installing `graphql-core-next`, as both libraries use `graphql` namespace.
- Added `gql()` utility that provides GraphQL string validation on declaration time, and enables use of [Apollo-GraphQL](https://marketplace.visualstudio.com/items?itemName=apollographql.vscode-apollo) plugin in Python code.
- Added `load_schema_from_path()` utility function that loads GraphQL types from file or directory containing `.graphql` files, also performing syntax validation.
- Added `start_simple_server()` shortcut function for a quick dev server creation, abstracting away the `GraphQLMiddleware.make_server()` from first time users.
- `Boolean` built-in scalar now checks the type of each serialized value. Returning values of type other than `bool`, `int` or `float` from a field resolver will result in a `Boolean cannot represent a non boolean value` error.
- Redefining type in `type_defs` will now result in `TypeError` being raised. This is breaking change from previous behaviour where old type was simply replaced with new one.
- Returning `None` from scalar `parse_literal` and `parse_value` function no longer results in GraphQL API producing default error message. Instead `None` will be passed further down to resolver or producing "value is required" error if its marked as such with `!` For old behaviour raise either `ValueError` or `TypeError`. See documentation for more details.
- `resolvers` argument defined by `GraphQLMiddleware.__init__()`, `GraphQLMiddleware.make_server()` and `start_simple_server()` is now optional, allowing for quick experiments with schema definitions.
- `dict` has been removed as primitive for mapping python function to fields. Instead, `make_executable_schema()` expects object or iterable of objects with `bind_to_schema` method, that is called with `GraphQLSchema` instance and are expected to add resolvers to schema.
- Default resolvers are no longer set implicitly by `make_executable_schema()`. Instead you expected to include either `ariadne.fallback_resolvers` or `ariadne.snake_case_fallback_resolvers` in the list of `resolvers` for your schema.
- Added `snake_case_fallback_resolvers` that populates schema with default resolvers that map `CamelCase` and `PascalCase` field names from schema to `snake_sase` names in Python.
- Added `ResolverMap` object that enables assignment of resolver functions to schema types.
- Added `Scalar` object that enables assignment of `serialize`, `parse_value` and `parse_literal` functions to custom scalars.
- Both `ResolverMap` and `Scalar` are validating if schema defines specified types and/or fields at moment of creation of executable schema, providing better feedback to developer.
