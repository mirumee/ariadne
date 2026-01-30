---
id: other-integrations
title: Other technologies
---

Ariadne can be used to add GraphQL server to projects developed using any web framework that supports JSON responses.

Implementation details differ between frameworks, but same steps apply for most of them:

1. Use [`make_executable_schema`](../API-reference/api-reference#make_executable_schema) to create executable schema instance.
2. Create view, route or controller (semantics vary between frameworks) that accepts `GET` and `POST` requests.
3. If request was made with `GET` method, return response containing GraphQL Playground's HTML.
4. If request was made with `POST`, disable any CSRF checks, test that its content type is `application/json` then parse its content as JSON. Return `400 BAD REQUEST` if this fails.
5. Call [`graphql_sync`](../API-reference/api-reference#graphql_sync) with schema, parsed JSON and any other options that are fit for your implementation.
6. [`graphql_sync`](../API-reference/api-reference#graphql_sync) returns tuple that has two values: `boolean` and `dict`. Use dict as data for JSON response, and boolean for status code. If boolean is `true`, set response's status code to `200`, otherwise it should be `400`

See the [Flask integration](flask-integration) for implementation of this algorithm using Flask framework.

## Asynchronous servers

If your server stack supports ASGI, you can use [`graphql`](../API-reference/api-reference#graphql) to execute GraphQL queries asynchronously and [`subscribe`](../API-reference/api-reference#subscribe) for websocket connections initialized by subscriptions.

## File uploads

To support file uploads, your `POST` method implementation will need to be extended to allow the [`multipart/form-data` requests](https://github.com/jaydenseric/graphql-multipart-request-spec), following algorithm supplied below:

1. Parse JSON stored in `operations` and `map` value of HTTP request. Return response with `400` status code if parsing of those values fails.
2. Create `dict` (or any Python object that implements `__getitem__`) that contains remaining query's values. If possible, filter off items that aren't an uploaded file.
3. Call [`combine_multipart_data`](../API-reference/api-reference#combine_multipart_data) with `operations`, `map` and data structure from step 2 as its values.
4. Call [`graphql`](../API-reference/api-reference#graphql) or [`graphql_sync`](../API-reference/api-reference#graphql_sync) with value returned by `combine_multipart_data`.

Rest of the algorithm is same as in regular queries.
