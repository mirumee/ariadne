# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ariadne is a Python library for implementing GraphQL servers using a **schema-first approach**. GraphQL schemas are defined in SDL (Schema Definition Language), and Python code is bound to the schema using bindable classes.

**Key principle**: Define your schema in SDL first, then bind Python resolvers and logic to it.

## Development Commands

We use [just](https://github.com/casey/just) for development commands and [Hatch](https://github.com/pypa/hatch) for project/environment management.

Run `just` (or `just --list`) to see all available commands.

```bash
# Run all checks (what CI runs) - use before creating a PR
just check

# Quick checks: format + types + tests (no integration tests)
just quick-check

# Format code (uses ruff)
just fmt
# or: hatch fmt

# Check formatting without modifying (CI uses this)
just fmt-check

# Type checking (ty - Astral's type checker)
just types
# or: hatch run types:check

# Run tests with coverage (default Python 3.10)
just test
# or: hatch test -c -py 3.10

# Run tests across all Python versions (3.10-3.14)
just test-all
# or: hatch test -a -p

# Full CI parity: all checks including full test matrix
just check-all

# Run all integration tests (FastAPI, Starlette, Flask)
just integration

# Run a single integration env
just integration-env test-integration-fastapi

# Run a single test file
hatch test tests/test_graphql.py

# Run a single test
hatch test tests/test_graphql.py::test_function_name

# Run benchmarks
hatch test benchmark --benchmark-storage=file://benchmark/results

# Generate coverage report (XML for Codecov)
just coverage
```

## Architecture

### Core Concepts

1. **Schema-First**: SDL strings define the GraphQL schema structure
2. **Bindables**: Python classes that bind logic to schema types (`ObjectType`, `EnumType`, `ScalarType`, etc.)
3. **Executable Schema**: `make_executable_schema()` combines SDL + bindables into a working GraphQL schema

### Key Modules

- `ariadne/executable_schema.py` - `make_executable_schema()` - the main entry point for creating schemas
- `ariadne/graphql.py` - `graphql()`, `graphql_sync()`, `subscribe()` - query execution functions
- `ariadne/objects.py` - `ObjectType`, `QueryType`, `MutationType` - object type binding
- `ariadne/subscriptions.py` - `SubscriptionType` - subscription type binding
- `ariadne/types.py` - Type definitions and protocols (`Extension`, `SchemaBindable`, `Resolver`)
- `ariadne/load_schema.py` - `load_schema_from_path()` - loading SDL from `.graphql` files
- `ariadne/asgi/graphql.py` - `GraphQL` ASGI application for running as a web server
- `ariadne/asgi/handlers/` - Protocol handlers (HTTP, GraphQL-WS, GraphQL-Transport-WS)
- `ariadne/wsgi.py` - WSGI middleware for Flask/Django integration

### Bindable Pattern

All type bindings follow the `SchemaBindable` protocol. Resolvers are added via decorators:

```python
from ariadne import QueryType, make_executable_schema

type_defs = """
    type Query {
        hello: String!
    }
"""

query = QueryType()

@query.field("hello")
def resolve_hello(_, info):
    return "Hello, World!"

schema = make_executable_schema(type_defs, query)
```

### Extension System

Extensions hook into the query execution lifecycle. See `ariadne/contrib/tracing/` for examples (Apollo Tracing, OpenTracing, OpenTelemetry).

### Directory Structure

```
ariadne/
├── asgi/              # ASGI server and WebSocket/SSE handlers
│   └── handlers/      # HTTP, GraphQL-WS, GraphQL-Transport-WS protocols
├── contrib/           # Optional features
│   ├── federation/    # Apollo Federation support (v1.0–v2.6)
│   ├── relay/         # GraphQL Relay support
│   ├── tracing/       # Tracing extensions (Apollo, OpenTracing, OpenTelemetry)
│   └── sse.py         # Server-Sent Events support
├── explorer/          # GraphQL explorers (GraphiQL, Apollo Sandbox, Playground)
└── validation/        # Query validation rules (introspection control, query cost)
```

### Test Structure

- `tests/` - Unit tests (pytest with strict asyncio mode)
- `tests/asgi/` - ASGI application and protocol handler tests
- `tests_integrations/` - Framework integration tests (FastAPI, Flask, Starlette)
- `tests_mypy/` - Type annotation validation tests (used with `ty` checker)
- `benchmark/` - Performance benchmarks (pytest-benchmark)

## Code Style

- **Python 3.10+** with type hints throughout
- **Ruff** for formatting and linting (line length 88)
- **ty** for type checking (Astral's fast type checker written in Rust)
- **90% minimum** test coverage required
- Lint rules: `E, F, G, I, N, Q, UP, C90, T20, TID` (see `pyproject.toml` for details)
- Max complexity: 15 (McCabe)

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature or functionality |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `build` | Changes to build system, dependencies, or project config |
| `ci` | Changes to CI configuration or scripts |
| `perf` | Performance improvements |
| `chore` | Maintenance tasks, housekeeping |

### Examples

```
feat: Add SSE support for GraphQL subscriptions
fix: Fix RelayObjectType returned object
docs: Update documentation structure to number prefixes
build: Introduce just (with justfile) for development and github actions
build: Replace mypy with ty
refactor: Replace hardcoded HTTP statuses with HTTPStatus
test: Add integration tests for Flask 3.0
```

### Guidelines

- Use lowercase for the description (no capital after the colon)
- Do not end the description with a period
- Use imperative mood ("add" not "added", "fix" not "fixed")
- Keep the first line under 72 characters
- Add a blank line and longer description body when the change needs more context

## CI Pipeline

CI runs on push to `main`, pull requests, and on schedule (Mon/Wed). The pipeline:

1. **Format check** (`just fmt-check`) - Ruff formatting validation
2. **Type checking** (`just types`) - ty type checker
3. **Tests** (`hatch test -c -py <version>`) - across Python 3.10–3.14
4. **Benchmarks** - performance regression tracking
5. **Integration tests** - FastAPI, Starlette, Flask (all Python versions)

## Documentation

See `docs/llms.txt` for a complete documentation navigation map for AI assistants. Key docs:

- `docs/01-Docs/01-intro.md` - Getting started guide
- `docs/01-Docs/02-resolvers.md` - How resolvers work
- `docs/01-Docs/16-modularization.md` - Organizing large schemas
- `docs/01-Docs/12-subscriptions.md` - Real-time subscriptions
- `docs/08-API-reference/01-api-reference.md` - Full API reference
- `docs/05-Integrations/` - Framework integration guides (Django, FastAPI, Flask, Starlette)
- `docs/06-Extensions/` - Extension system, middleware, query validators
