---
id: aws-lambda
title: AWS Lambda
---

# AWS Lambda

Multiple ways to implement an AWS Lambda function for GraphQL using Ariadne exist.

This document presents a selected few of those, but its aim is not to be an __exhaustive__ list of all approaches to using Ariadne on AWS Lambda.

## Deploying ASGI Application with Ariadne Lambda

Ariadne Lambda is an extension to Ariadne itself to enable running [ASGI](asgi.md) applications on AWS Lambda:

```python
from typing import Any

from ariadne import QueryType, gql, make_executable_schema
from ariadne_lambda.graphql import GraphQLLambda
from asgiref.sync import async_to_sync
from aws_lambda_powertools.utilities.typing import LambdaContext

type_defs = gql(
    """
    type Query {
        hello: String!
    }
""")
query = QueryType()

@query.field("hello")
def resolve_hello(_, info):
    request = info.context["request"]
    user_agent = request.headers.get("user-agent", "guest")
    return "Hello, %s!" % user_agent

schema = make_executable_schema(type_defs, query)
graphql_app = GraphQLLambda(schema=schema)

def graphql_http_handler(event: dict[str, Any], context: LambdaContext):
    return async_to_sync(graphql_app)(event, context)
```

This approach is recommended because it gives immediate availability of Ariadne's features through the `GraphQL` object's options and doesn't require the implementation of a custom translation layer between the GraphQL engine and AWS Lambda.

> **Note:** If you need your Lambda function to offer other API endpoints in addition to GraphQL, you can combine your Ariadne app with [Starlette](starlette-integration.md) or [FastAPI](fastapi-integration.md) along with [Lynara](https://github.com/mirumee/lynara), which wraps the app to handle HTTP requests from AWS.

## Minimal Lambda Handler Example

If you want to skip the HTTP stack altogether, you can execute the queries directly using the [`graphql_sync`](api-reference.md#graphql_sync):

```python
import json
import logging

from ariadne import QueryType, graphql_sync, make_executable_schema, gql

logger = logging.getLogger()

type_defs = gql(
    """
    type Query {
        hello: String!
    }
""")

query_type = QueryType()

@query_type.field("hello")
def resolve_hello(_, info):
    http_context = info.context["requestContext"]["http"]
    user_agent = http_context.get("userAgent") or "Anon"
    return f"Hello {user_agent}!"

schema = make_executable_schema(type_defs, query_type)

def handler(event: dict, _):
    try:
        data = json.loads(event.get("body") or "")
    except ValueError as exc:
        return response({"error": f"Failed to parse JSON: {exc}"}, 405)

    success, result = graphql_sync(
        schema,
        data,
        context_value=event,
        logger=logger,
    )

    return response(result, 200 if success else 400)

def response(body: dict, status_code: int = 200):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }
```

This Lambda function will expect a JSON request with at least one key, a `query` containing the GraphQL query.

### Asynchronous Example

In case you want to run your handler asynchronously, you'll need to run it in an event loop.

This can be done manually or by decorating the async handler with the `async_to_sync` decorator from the `asgiref` package:

```python
import json
import logging

from ariadne import QueryType, graphql, make_executable_schema, gql
from asgiref.sync import async_to_sync

logger = logging.getLogger()

type_defs = gql(
    """
    type Query {
        hello: String!
    }
""")

query_type = QueryType()

@query_type.field("hello")
def resolve_hello(_, info):
    http_context = info.context["requestContext"]["http"]
    user_agent = http_context.get("userAgent") or "Anon"
    return f"Hello {user_agent}!"

schema = make_executable_schema(type_defs, query_type)

@async_to_sync
async def handler(event: dict, _):
    try:
        data = json.loads(event.get("body") or "")
    except ValueError as exc:
        return response({"error": f"Failed to parse JSON: {exc}"}, 405)

    success, result = await graphql(
        schema,
        data,
        context_value=event,
        logger=logger,
    )

    return response(result, 200 if success else 400)

def response(body: dict, status_code: int = 200):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }
```

## Local Testing

If you want to test your Lambda functions locally, you can use the repository [Smyth](https://github.com/mirumee/smyth), which supports local development of Lambdas. This allows you to simulate the AWS Lambda environment on your local machine, making it easier to develop and debug your functions before deploying them to AWS.
