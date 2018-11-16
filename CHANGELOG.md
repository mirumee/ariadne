# CHANGELOG

## 0.2.0 (UNRELEASED)

- Removed support for Python 3.5 and added support for 3.7
- Moved to `GraphQL-core-next` that supports more recent GraphQL spec, as well as supports `async`.
- Returning `None` from scalar `parse_literal` and `parse_value` function no longer results in GraphQL API producing default error message. Instead `None` will be passed further down to resolver or producing "value is required" error if its marked as such with `!` For old behaviour raise either `ValueError` or `TypeError`. See documentation for more details.