# CHANGELOG

All notable unreleased changes to this project will be documented in this file.

For released versions, see the [Releases](https://github.com/mirumee/ariadne/releases) page.

## Unreleased

### Fixed

- Query cost validation now uses the length of list and tuple arguments named in `multipliers`. Queries that previously passed may exceed `maximum_cost` after upgrading; review affected query costs and thresholds before deployment.
