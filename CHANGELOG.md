# CHANGELOG

## 0.6.0 (2019-08-12)

- Updated `graphql-core-next` to 1.1.1 which has feature parity with GraphQL.js 14.4.0.
- Added basic extensions system to the `ariadne.graphql.graphql`. Currently only available in the `ariadne.asgi.GraphQL` app.
- Added `convert_kwargs_to_snake_case` utility decorator that recursively converts the case of arguments passed to resolver from `camelCase` to `snake_case`.
- Removed `default_resolver` and replaced its uses in library with `graphql.default_field_resolver`.
- Resolver returned by `resolve_to` util follows `graphql.default_field_resolver` behaviour and supports resolving to callables.
- Added `is_default_resolver` utility for checking if resolver function is `graphql.default_field_resolver`, resolver created with `resolve_to` or `alias`.
- Added `ariadne.contrib.tracing` package with `ApolloTracingExtension` and `OpenTracingExtension` GraphQL extensions for adding Apollo tracing and OpenTracing monitoring to the API (ASGI only).
- Updated ASGI app disconnection handler to also check client connection state.
- Fixed ASGI app `context_value` option support for async callables.
- Updated `middleware` option implementation in ASGI and WSGI apps to accept list of middleware functions or callable returning those.
- Moved error formatting utils (`get_formatted_error_context`, `get_formatted_error_traceback`, `unwrap_graphql_error`) to public API.


## 0.5.0 (2019-06-07)

- Added support for file uploads.


## 0.4.0 (2019-05-23)

- Updated `graphql-core-next` to 1.0.4 which has feature parity with GraphQL.js 14.3.1 and better type annotations.
- `ariadne.asgi.GraphQL` is now an ASGI3 application. ASGI3 is now handled by all ASGI servers.
- `ObjectType.field` and `SubscriptionType.source` decorators now raise ValueError when used without name argument (eg. `@foo.field`).
- `ScalarType` will now use default literal parser that unpacks `ast.value` and calls value parser if scalar has value parser set.
- Updated ``ariadne.asgi.GraphQL`` and ``ariadne.wsgi.GraphQL`` to support callables for ``context_value`` and ``root_value`` options.
- Added ``logger`` option to ``ariadne.asgi.GraphQL``, ``ariadne.wsgi.GraphQL`` and ``ariadne.graphql.*`` utils.
- Added default logger that logs to ``ariadne``.
- Added support for `extend type` in schema definitions.
- Removed unused `format_errors` utility function and renamed `ariadne.format_errors` module to `ariadne.format_error`.
- Removed explicit `typing` dependency.
- Added `ariadne.contrib.django` package that provides Django class-based view together with `Date` and `Datetime` scalars.
- Fixed default ENUM values not being set.
- Updated project setup so mypy ran in projects with Ariadne dependency run type checks against it's annotations.
- Updated Starlette to 0.12.0.


## 0.3.0 (2019-04-08)

- Added `EnumType` type for mapping enum variables to internal representation used in application.
- Added support for subscriptions.
- Updated Playground to 1.8.7.
- Split `GraphQLMiddleware` into two classes and moved it to `ariadne.wsgi`.
- Added an ASGI interface based on Starlette under `ariadne.asgi`.
- Replaced the simple server utility with Uvicorn.
- Made users responsible for calling `make_executable_schema`.
- Added `UnionType` and `InterfaceType` types.
- Updated library API to be more consistent between types, and work better with code analysis tools like PyLint. Added `QueryType` and `MutationType` convenience utils. Suffixed all types names with `Type` so they are less likely to clash with other libraries built-ins.
- Improved error reporting to also include Python exception type, traceback and context in the error JSON. Added `debug` and `error_formatter` options to enable developer customization.
- Introduced Ariadne wrappers for `graphql`, `graphql_sync`, and `subscribe` to ease integration into custom servers.


## 0.2.0 (2019-01-07)

- Removed support for Python 3.5 and added support for 3.7.
- Moved to `GraphQL-core-next` that supports `async` resolvers, query execution and implements a more recent version of GraphQL spec. If you are updating an existing project, you will need to uninstall `graphql-core` before installing `graphql-core-next`, as both libraries use `graphql` namespace.
- Added `gql()` utility that provides GraphQL string validation on declaration time, and enables use of [Apollo-GraphQL](https://marketplace.visualstudio.com/items?itemName=apollographql.vscode-apollo) plugin in Python code.
- Added `load_schema_from_path()` utility function that loads GraphQL types from a file or directory containing `.graphql` files, also performing syntax validation.
- Added `start_simple_server()` shortcut function for quick dev server creation, abstracting away the `GraphQLMiddleware.make_server()` from first time users.
- `Boolean` built-in scalar now checks the type of each serialized value. Returning values of type other than `bool`, `int` or `float` from a field resolver will result in a `Boolean cannot represent a non boolean value` error.
- Redefining type in `type_defs` will now result in `TypeError` being raised. This is a breaking change from previous behavior where the old type was simply replaced with a new one.
- Returning `None` from scalar `parse_literal` and `parse_value` function no longer results in GraphQL API producing default error message. Instead, `None` will be passed further down to resolver or produce a "value is required" error if its marked as such with `!` For old behavior raise either `ValueError` or `TypeError`. See documentation for more details.
- `resolvers` argument defined by `GraphQLMiddleware.__init__()`, `GraphQLMiddleware.make_server()` and `start_simple_server()` is now optional, allowing for quick experiments with schema definitions.
- `dict` has been removed as primitive for mapping python function to fields. Instead, `make_executable_schema()` expects object or list of objects with a `bind_to_schema` method, that is called with a `GraphQLSchema` instance and are expected to add resolvers to schema.
- Default resolvers are no longer set implicitly by `make_executable_schema()`. Instead you are expected to include either `ariadne.fallback_resolvers` or `ariadne.snake_case_fallback_resolvers` in the list of `resolvers` for your schema.
- Added `snake_case_fallback_resolvers` that populates schema with default resolvers that map `CamelCase` and `PascalCase` field names from schema to `snake_case` names in Python.
- Added `ResolverMap` object that enables assignment of resolver functions to schema types.
- Added `Scalar` object that enables assignment of `serialize`, `parse_value` and `parse_literal` functions to custom scalars.
- Both `ResolverMap` and `Scalar` are validating if schema defines specified types and/or fields at the moment of creation of executable schema, providing better feedback to the developer.
