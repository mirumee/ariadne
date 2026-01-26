---
id: query-stack
title: Customizing Query Stack
---

Ariadne lets to developers to replace both parsing and validating steps of the query execution stack with custom logic.


## Query parser

Default GraphQL query parser used by Ariadne is the `parse` function from the `graphql-core` package:

```python
from graphql import parse

document = parse("{ query string }")
```

This function takes the `str` with the GraphQL query, and parsers it into a `DocumentNode` instance containing the GraphQL AST representation of the query.

Ariadne's `GraphQL()` ASGI and WSGI apps together with `graphql()`, `graphql_sync()` and `subscribe()` functions accept the `query_parser` named argument that lets server developers to provide a custom function to use for parsing queries.

If custom parser is set, this parser is called with two arguments:

- `context: ContextValue`
- `data: dict[str, Any]`: a `dict` with current operation's payload (`query`, `operationName` and `variables`).

Here's an example custom parser function that only parses the `query` string from query's payload:

```python
from ariadne.types import ContextValue
from graphql import DocumentNode, parse


def caching_query_parser(context: ContextValue, data: dict[str, Any]) -> DocumentNode:
    return parse(data["query"])
```


## Query validation

Ariadne's GraphQL query validation uses the `validate` function from the `graphql-core` package to validate a query against a schema and a set of rules. This function can be swapped out in GraphQL servers using the `query_validator` option.

Custom validator should have a following signature:

```python
from typing import Collection, Type

from graphql import (
    GraphQLSchema,
    DocumentNode,
    ASTValidationRule,
    TypeInfo,
)


def custom_query_validator(
    schema: GraphQLSchema,
    document_ast: DocumentNode,
    rules: Collection[Type[ASTValidationRule]] | None = None,
    max_errors: int | None = None,
    type_info: TypeInfo | None = None,
) -> list[GraphQLError]:
    return []  # List of `GraphQLError`s with problems with the query
```


## Examples


### Caching parsed queries

Following example shows a custom query parser that caches a number of GraphQL queries using the LRU approach. This parser will raise memory usage of the GraphQL server, but will improve query response times:

```python
from functools import lru_cache

from ariadne.types import ContextValue
from graphql import DocumentNode, parse


parse_cached = lru_cache(maxsize=64)(parse)


def caching_query_parser(context: ContextValue, data: dict[str, Any]) -> DocumentNode:
    # Custom parser function is called with the context and entire query's payload.
    return parse_cached(data["query"])


# Pass the 'caching_query_parser' to the 'query_parser' option of the 'GraphQL'
graphql = GraphQL(schema, query_parser=caching_query_parser)
```


### Combined parse and validation cache

The below code combines custom parser and validator functions to add caching to both query parsing and validation parts of the Query Stack:

```python
from collections.abc import Collection
from functools import lru_cache
from typing import Any

from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.graphql import validate_query
from ariadne.types import ContextValue
from graphql import ASTValidationRule, DocumentNode, GraphQLError, GraphQLSchema, TypeInfo, parse


parse_cached = lru_cache(maxsize=64)(parse)


def caching_query_parser(context: ContextValue, data: dict[str, Any]) -> DocumentNode:
    # Custom parser function is called with the context and entire query's payload.
    return parse_cached(data["query"])


validate_query_cached = lru_cache(maxsize=64)(validate_query)


def caching_query_validator(
    schema: GraphQLSchema,
    document_ast: DocumentNode,
    rules: Collection[type[ASTValidationRule]] | None = None,
    max_errors: int | None = None,
    type_info: TypeInfo | None = None,
) -> list[GraphQLError]:
    return validate_query_cached(
        schema=schema,
        document_ast=document_ast,
    )


# Add type definitions, resolvers, etc...
schema = make_executable_schema("...")

# Using our custom functions for parsing & validation
graphql = GraphQL(
    schema,
    query_parser=caching_query_parser,
    query_validator=caching_query_validator,
)
```
