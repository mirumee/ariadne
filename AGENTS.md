# Ariadne

## Quick Reference Commands

### Essential Development Commands

```bash
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
```

### Testing Commands

```bash
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

### Running Examples

Use `uv` to run examples from the `examples/` directory. Refer to the docstrings within each example file for specific commands.
Every example should include an example command of running a particular example with uvicorn.
```bash
# Run a basic query example
uv run examples/basic_query_example.py

# Run an ASGI example with uvicorn
uv run --with "uvicorn[standard]" --with ariadne \
    uvicorn examples.basic_query_example:app --reload
```

## Code Style Requirements

- **Python 3.10+** with type hints throughout
- **Ruff** for formatting and linting (line length 88)
- **ty** for type checking
- **90% minimum** test coverage required
- Max complexity: 15 (McCabe)

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>
```

### Commit Types

| Type | Usage |
|------|-------|
| `feat` | New feature or functionality |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `build` | Changes to build system, dependencies, or project config |
| `ci` | Changes to CI configuration or scripts |
| `perf` | Performance improvements |
| `chore` | Maintenance tasks, housekeeping |

### Commit Guidelines

- Use lowercase for the description (no capital after the colon)
- Do not end the description with a period
- Use imperative mood ("add" not "added", "fix" not "fixed")
- Keep the first line under 72 characters
- Always suggest a commit message when work is complete

## Final Checklist
1. Run `just check` to ensure all CI checks pass
2. Ensure test coverage meets the 90% minimum requirement
3. Format code with `just fmt`
4. Verify type hints with `just types`
5. Ensure the documentation is up-to-date
6. Write a clear commit message following the conventional commits format

