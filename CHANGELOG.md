# CHANGELOG

## 0.25.1 (2025-02-03)
- Fixed returned object for RelayObjectType


## 0.25 (2025-02-03)

- Added support for GraphQL subscriptions over the Server-Sent Events (SSE).
- Added support for GraphQL Relay


## 0.24 (2024-12-19)

- Added validation for directive declarations in `make_executable_schema` to prevent schema creation with undeclared directives.
- Replaced hardcoded HTTP statuses with `HTTPStatus` from the `http` stdlib module.
- Added `include_cookies` option to the `ExplorerApollo`.
- Fixed typing on `extract_data_from_request` method.
- Fixed tests websockets after starlette update.
- Added `share_enabled` param to `ExplorerPlayground` to enable share playground feature.
- Added support for nested attribute resolution in alias resolvers.
- Replaced regexes in the Apollo Federation implementation with cleaner approach using GraphQL AST.


## 0.23 (2024-03-18)

- Added `execute_get_queries` setting to the `GraphQL` apps that controls execution of the GraphQL "query" operations made with GET requests. Defaults to `False`.
- Added support for the Apollo Federation versions up to 2.6.
- Fixed deprecation warnings in Apollo Tracing extension.
- Added a check to prevent `subscription` operation execution when query is made with POST request.


## 0.22 (2024-01-31)

- Deprecated `EnumType.bind_to_default_values` method. It will be removed in a future release.
- Added `repair_schema_default_enum_values` to public API.
- Removed `validate_schema_enum_values` and introduced `validate_schema_default_enum_values` in its place. This is a breaking change.
- Fixed an invalid error message returned by the `GraphQLTransportWSHandler` for `query` and `mutation` operations.


## 0.21 (2023-11-08)

- Added Python 3.12 to tested versions.
- Updated integration tests to run against FastAPI 0.104, Flask 3.0 and Starlette 0.32.
- Updated GraphiQL explorer to initialize with support for subscriptions.


## 0.20.1 (2023-06-27)

- Updated the GraphiQL template with working explorer plugin URL.


## 0.20 (2023-06-21)

- Dropped support for Python 3.7.
- Added `OpenTelemetry` and `opentelemetry_extension` extension, importable form `ariadne.tracing.opentelemetry`.
- Added `query_validator` option to ASGI and WSGI `GraphQL` applications that enables customization of query validation step.
- Fixed `ERROR` message in GraphQL-WS protocol having invalid payload type.
- Fixed query cost validator incorrect handling of inline fragments.
- Fixed `make_executable_schema` error when `null` is used as default value for `input` typed field argument.
- Updated default GraphiQL2 template to use production build of React.js.
- Removed `ExtensionSync`. `Extension` now supports both async and sync contexts.
- Removed `OpenTracingSync` and `opentracing_extension_sync`. `OpenTracing` and `opentracing_extension` now support both async and sync contexts.
- Removed `ApolloTracingSync`. `ApolloTracing` now supports both async and sync contexts.


## 0.19.1 (2023-03-28)

- Fixed `.graphql` definitions files not being included in the dist files


## 0.19.0 (2023-03-27)

- Added `InputType` for setting Python representations of GraphQL Input types
- Added support for passing `Enum` types directly to `make_executable_schema`
- Added `convert_names_case` option to `make_federated_schema`.
- Added support for the `@interfaceObject` directive in Apollo Federation.
- Fixed federation support for directives without surrounding whitespace.


## 0.18.1 (2023-02-22)

- Fixed type annotations on `EnumType`.


## 0.18.0 (2023-02-21)

- GraphiQL2 is now default API explorer.
- Added `explorer` option to ASGI and WSGI `GraphQL` applications that enables API explorer customization.
- Added `ExplorerHttp405` API explorer that returns `405 Method Not Allowed` for GET HTTP requests.
- Added implementations for GraphiQL2, GraphQL-Playground and Apollo Sandbox explorers.
- Added `convert_names_case` option to `make_executable_schema` to convert all names in schema to Python case using default or custom strategy.
- Added support for `Path`-like objects to `load_schema_from_path`.
- Changed `logger` option to also support `Logger` and `LoggerAdapter` instance in addition to `str` with logger name.
- Added support for `@tag` directive used by Apollo Federation.
- Moved project configuration from `setup.py` to `pyproject.toml`.
- Changed `context_value` option in ASGI and WSGI applications for callables to take query data as second argument.
- Changed `root_value` option in ASGI and WSGI applications for callables to take operation and and variables in addition to context and parsed query.
- Added `execution_context_class` option to ASGI and WSGI applications.
- Added `query_parser` option to ASGI and WSGI `GraphQL` applications that enables query parsing customization.
- Changed `middleware` option to work with callable or list of middlewares instead of `MiddlewareManager` instance.
- Added `middleware_manager_class` option to ASGI and WSGI applications.
- Added `handle_request` and `handle_websocket` methods to `ASGI` application that takes Starlette/FastAPI `Request` and `Websocket` objects.
- Fixed type annotations for middlewares.
- Added docstrings to members of public API.


## 0.17.1 (2023-01-09)

- Fixed an error when schema that defines an interface type with fields having enum arguments with default values (eg. `field(arg: Enum = ENUM_MEMBER)`) is introspected.


## 0.17.0 (2022-12-14)

- Bumped starlette dependency in setup.py to `<1.0`.
- Added Python 3.11 to test matrix.
- Removed usage of deprecated `cgi` module.
- Renamed `asgi-file-uploads` optional dependency to `file-uploads`.


## 0.16.1 (2022-09-26)

- Fixed `GraphQLTransportWSHandler` implementation to handle multiple connections.


## 0.16.0 (2022-09-08)

- Refactored `ariadne.asgi.GraphQL` to use strategy pattern for handling HTTP and WebSockets.
- Updated `load_schema_from_path` to also support `.gql` and `.graphqls` files.
- Added support for `starlette` 0.20.


## 0.15.1 (2022-04-22)

- Fix performance regression in `make_federated_schema`.


## 0.15.0 (2022-04-13)

- Updated `graphql-core` requirement to 3.2.0.
- Bumped `starlette` supported versions to 0.18 and 0.19.
- Drop Python 3.6 support.
- Added basic support for `OPTIONS` HTTP request.
- Refactor `ariadne.asgi.GraphQL` to make it easier to customize JSON response.
- Added `trace_default_resolver` to `ApolloTracingExtension` that enables tracing for default resolvers.
- Fixed `make_federated_schema` error when custom directive in schema has description.
- Moved `set_default_enum_values_on_schema`, `validate_schema_enum_values` and `type_implements_interface` to public API.
- Changed `graphql_sync` to use `execute_sync` instead of `execute`.
- Added `on_operation` hook to `ariadne.asgi.GraphQL` that's called when individual subscription operation is started.
- Added `on_complete` hook to `ariadne.asgi.GraphQL` that's called when individual subscription operation is completed.
- Updated `on_disconnect` hook so its called in Webhook handler's `finally` clause, making it called in more situations.
- Marked `Extension`, `ExtensionSync` and `SchemaBindable` protocols as `@runtime_checkable`.
- Renamed `parent` to `obj` in `ApolloTracing` and `OpenTracing` extensions so arg name won't cause conflict when custom resolver has `parent` arg.


## 0.14.1 (2022-01-28)

- Remove `ariadne.contrib.django` from release.
- Lock `GraphQL-core` requirement at <3.2.


## 0.14.0 (2021-11-24)

- Added `on_connect` and `on_disconnect` options to `ariadne.asgi.GraphQL`, enabling developers to run additional initialization and cleanup for websocket connections.
- Updated Starlette dependency to 0.17.1.
- Added support for multiple keys for GraphQL federations.
- Made `Query` type optional in federated schemas.
- Updated default resolvers to test for `Mapping` instead of `dict`.
- Removed `ariadne.contrib.django`. (Use [ariadne_django](https://github.com/reset-button/ariadne_django) instead).
- Updated query cost validator to handle optional variables.


## 0.13.0 (2021-03-17)

- Updated `graphql-core` requirement to 3.1.3.
- Added support for Python 3.9.
- Added support for using nested variables as cost multipliers in the query price validator.
- `None` is now correctly returned instead of `{"__typename": typename}` within federation.
- Fixed some surprising behaviors in `convert_kwargs_to_snake_case` and `snake_case_fallback_resolvers`.


## 0.12.0 (2020-08-04)

- Added `validation_rules` option to query executors as well as ASGI and WSGI apps and Django view that allow developers to include custom query validation logic in their APIs.
- Added `introspection` option to ASGI and WSGI apps, allowing developers to disable GraphQL introspection on their server.
- Added `validation.cost_validator` query validator that allows developers to limit maximum allowed query cost/complexity.
- Removed default literal parser from `ScalarType` because GraphQL already provides one.
- Added `extensions` and `introspection` configuration options to Django view.
- Updated requirements list to require `graphql-core` 3.


## 0.11.0 (2020-04-01)

- Fixed `convert_kwargs_to_snake_case` utility so it also converts the case in lists items.
- Removed support for sending queries and mutations via WebSocket.
- Freezed `graphql-core` dependency at version 3.0.3.
- Unified default `info.context` value for WSGI to be dict with single `request` key.


## 0.10.0 (2020-02-11)

- Added support for `Apollo Federation`.
- Added the ability to send queries to the same channel as the subscription via WebSocket.


## 0.9.0 (2019-12-11)

- Updated `graphql-core-next` to `graphql-core` 3.


## 0.8.0 (2019-11-25)

- Added recursive loading of GraphQL schema files from provided path.
- Added support for passing multiple bindables as `*args` to `make_executable_schema`.
- Updated Starlette dependency to 0.13.
- Made `python-multipart` optional dependency for `asgi-file-uploads`.
- Added Python 3.8 to officially supported versions.


## 0.7.0 (2019-10-03)

- Added support for custom schema directives.
- Added support for synchronous extensions and synchronous versions of `ApolloTracing` and `OpenTracing` extensions.
- Added `context` argument to `has_errors` and `format` hooks.


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
