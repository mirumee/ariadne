# CHANGELOG

All notable unreleased changes to this project will be documented in this file.

For released versions, see the [Releases](https://github.com/mirumee/ariadne/releases) page.

## 1.0.0 (2026-03-16)

### ⚠️ Breaking Changes
- **Remove deprecated `EnumType.bind_to_default_values`**
- **Remove deprecated apollo tracing, opentracing, and extend_federated_schema**
- **Make base handler class names consistent**
- **Make convert_names_case handle digit boundaries in lowercase names**

### 🐛 Bug Fixes
- Add subresource integrity (SRI) to GraphiQL explorer scripts
- Add missing permission
- Return correct success value when errors occurs
- Fix GraphQL.get_request_data return type
- Make convert_names_case run before directives in make_executable_schema

### 📚 Documentation
- Get rid of deprecated. Fix llms.txt paths
- Fixing styles, typos. Cleanups
- Update typing in api references
- Add more examples
- Fix description for string-based enums

### 🛠️ Build System
- Update classifiers and versioning policy
- Add git-cliff for automated changelog and release notes

---

## Migration Guide: 0.29.0 → 1.0.0

### Removed `EnumType.bind_to_default_values`

The `EnumType.bind_to_default_values()` method, deprecated since 0.22, has been removed. `make_executable_schema` already calls `repair_schema_default_enum_values` internally, so the manual call is unnecessary.

**Migration:** Remove the call entirely.

```python
# Before
from ariadne import EnumType, make_executable_schema

status_type = EnumType("Status", {"ACTIVE": 1, "INACTIVE": 0})
schema = make_executable_schema(type_defs, status_type)
status_type.bind_to_default_values(schema)  # ← remove this line

# After
from ariadne import EnumType, make_executable_schema

status_type = EnumType("Status", {"ACTIVE": 1, "INACTIVE": 0})
schema = make_executable_schema(type_defs, status_type)
# Default enum values are now repaired automatically
```

### Removed deprecated tracing & federation utilities

The following modules and functions have been removed:

- `ApolloTracingExtension` / `apollo_tracing_extension()` from `ariadne.contrib.tracing.apollotracing`
- `OpenTracingExtension` / `opentracing_extension()` from `ariadne.contrib.tracing.opentracing`
- `extend_federated_schema()` from `ariadne.contrib.federation.schema`
- The `tracing` pip extra (`pip install ariadne[tracing]`) has been removed

**Migration (tracing):** Both Apollo Tracing and OpenTracing are archived projects. Migrate to OpenTelemetry using the `telemetry` extra:

```python
# Before
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension
# or
from ariadne.contrib.tracing.opentracing import OpenTracingExtension

# After
pip install ariadne[telemetry]

from ariadne.contrib.tracing.opentelemetry import OpenTelemetryExtension
```

**Migration (`extend_federated_schema`):** Use `graphql.extend_schema()` from graphql-core directly:

```python
# Before
from ariadne.contrib.federation.schema import extend_federated_schema

schema = extend_federated_schema(schema, type_defs)

# After
from graphql import build_ast_schema, extend_schema, parse

schema = extend_schema(schema, parse(type_defs))
```

### Renamed base handler classes

Base handler class names have been made consistent:

| Old Name | New Name |
|----------|----------|
| `GraphQLHandler` | `GraphQLHandlerBase` |
| `GraphQLWebsocketHandler` | `GraphQLWebsocketHandlerBase` |

`GraphQLHttpHandlerBase` was already correctly named and is unchanged.

**Migration:** Find-and-replace your imports. This only affects users subclassing these base handlers.

```python
# Before
from ariadne.asgi.handlers import GraphQLHandler, GraphQLWebsocketHandler

class MyHandler(GraphQLHandler): ...
class MyWSHandler(GraphQLWebsocketHandler): ...

# After
from ariadne.asgi.handlers import GraphQLHandlerBase, GraphQLWebsocketHandlerBase

class MyHandler(GraphQLHandlerBase): ...
class MyWSHandler(GraphQLWebsocketHandlerBase): ...
```

### `convert_names_case` now handles digit boundaries

`convert_names_case` now inserts underscores at digit boundaries in lowercase names. Previously, names that were already lowercase were skipped entirely. Now the custom name converter is called for **all** fields, including already-lowercase ones.

Examples of changed behavior:

| GraphQL name | Before | After |
|-------------|--------|-------|
| `foobar19` | `foobar19` | `foobar_19` |
| `test134` | `test134` | `test_134` |
| `134test` | `134test` | `134_test` |

**Migration:** If you rely on the old behavior (no underscores at digit boundaries), pass a custom `name_converter` to `make_executable_schema`:

```python
from ariadne import make_executable_schema

def my_name_converter(graphql_name: str, schema) -> str:
    # Your custom logic here — return the name unchanged
    # to preserve old behavior for digit boundaries
    return graphql_name

schema = make_executable_schema(
    type_defs, ..., name_converter=my_name_converter
)
```
