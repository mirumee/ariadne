# Ariadne development commands
# Run `just --list` to see all available recipes

# Default: run to show all available commands in justfile
default:
    just --list

# Run all checks - match CI (format, types, tests, integration)
# Contributors: run this before creating a pull request
check: fmt-check types test integration

# Full CI parity: all checks including tests across all Python versions (slower)
check-all: fmt-check types test-all integration

# Format code with ruff
fmt:
    hatch fmt

# Check code formatting (CI)
fmt-check:
    hatch fmt --check

# Run type checking
types:
    hatch run types:check

# Run tests with coverage for default Python version
test:
    hatch test -c -py 3.10

# Run tests across all Python versions (3.10–3.14)
test-all:
    hatch test -a -p

# Run all integration tests
integration:
    hatch run test-integration-fastapi:test
    hatch run test-integration-starlette:test
    hatch run test-integration-flask:test

# Run single integration test (CI matrix: test-integration-fastapi, test-integration-starlette, test-integration-flask)
integration-env env:
    hatch run {{env}}:test

# Generate coverage report and XML (for Codecov)
coverage:
    hatch test --cover -i python=3.10
    hatch run coverage:xml

# Quick check: format + types + single Python version tests (faster than full check)
quick-check: fmt-check types test

# Preview unreleased commits as they would appear in the next release (no file changes)
changelog-preview:
    git cliff --unreleased --strip all

# Update CHANGELOG.md with current unreleased commits (regenerates the unreleased section)
changelog-update:
    git cliff --unreleased -o CHANGELOG.md

# Preview release notes for the latest stable tag (as they would appear on GitHub)
release-notes:
    git cliff --latest --strip all
