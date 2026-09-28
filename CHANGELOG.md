# CHANGELOG

All notable unreleased changes to this project will be documented in this file.

For released versions, see the [Releases](https://github.com/mirumee/ariadne/releases) page.

## Unreleased

- Cap `graphql-core` to `<3.3.0`. Version 3.3.0 removed `ExecutionContext` in
  favour of a rewritten `Executor`, so `import ariadne` failed outright with
  `ImportError: cannot import name 'ExecutionContext' from 'graphql'`. The
  `execution_context_class` option is part of Ariadne's public API and is used
  by `graphql-sync-dataloaders`, which has not been migrated to the new
  execution layer yet, so 3.3.0 cannot be supported without breaking it.
  Fresh installations now resolve to 3.2.x again.

