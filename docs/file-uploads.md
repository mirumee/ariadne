---
id: file-uploads
title: File uploads
---

Ariadne implements the [GraphQL multipart request specification](https://github.com/jaydenseric/graphql-multipart-request-spec) that describes how file uploads should be implemented by both API clients and servers.


> **Note**
>
> File uploads require `python-multipart` library:
>
> ```console
> pip install "ariadne[file-uploads]"
> ```


## Enabling file uploads

To enable file uploads on your server, define new a scalar named `Upload` in your schema:

```graphql
scalar Upload
```

Next, import `upload_scalar` from `ariadne` package and use it during the creation of your executable schema:

```python
from ariadne import make_executable_schema, upload_scalar

# ...your types definitions

schema = make_executable_schema(type_defs, [..., upload_scalar])
```

You will now be able to use `Upload` scalar arguments for your operations:

```graphql
type Mutation {
    uploadUserImage(image: Upload!): Boolean!
}
```


## Limitations

The default `Upload` scalar is a write-only scalar that supports only accessing the value that was passed through the `variables`. It is not possible to use it as return value for a GraphQL field or set its value in a GraphQL Query:

```graphql
type User {
    "This field will fail with ValueError"
    image: Upload
}
```

```graphql
mutation {
    uploadUserImage(image: "data:text/plain;base64,QXJpYWRuZSByb2NrcyE=")
}
```

> You are not required to use the `Upload` scalar implementation provided by Ariadne. You can implement your own if you wish to, so you can (for example) support file literals as base64 data.


## Implementation differences

The Python value returned by the `Upload` scalar is not standardized and depends on your technology stack:


### `ariadne.asgi`

Ariadne's ASGI support is based on [Starlette](https://starlette.io) and hence uploaded files are instances of [`UploadFile`](https://www.starlette.io/requests/#request-files).


### `ariadne.wsgi`

Ariadne's WSGI support uses the `python-multipart` library that represents uploaded files as instances of [`File`](https://github.com/andrew-d/python-multipart/blob/f1a275e73763d16a9dba45e2bd568860302786bd/multipart/multipart.py#L262).
