---
id: apollo-federation
title: Apollo Federation
---

[Apollo Federation](https://www.apollographql.com/docs/apollo-server/federation/introduction/) is an approach for composing multiple GraphQL services into one data graph, queryable from a single GraphQL server.

Ariadne supports building federated schemas through use of special [types and directives introduced by federation specification](https://www.apollographql.com/docs/apollo-server/federation/federation-spec/) that instruct Ariadne how it's GraphQL schema types and fields combine with types and fields defined in other GraphQL schemas forming the Federation.


## Federated architecture example

Let's say we have three separate GraphQL services that we want to convert into a federated service:

Users Service:

```graphql
type Query {
  me: User
}

type User {
  id: ID!
  name: String
  email: String!
}
```

Reviews Service:

```graphql
type Query {
  reviews(first: Int = 5): [Review]
}

type Review {
  id: ID!
  body: String
}
```

Products Service:

```graphql
type Query {
  topProducts(first: Int = 5): [Product]
}

type Product {
  upc: String!
  name: String
  price: Int
  weight: Int
}
```

Our goal is to add a connection between each of them and combine the above services into a single graph.

First, we need to add the `@key` directive to a type's definition as to allow other services to refer to it, or extend that type. This directive tells other services which fields to use in order to uniquely identify a particular instance of the type.

In our case, we should add it to the `User`, `Review` and `Product` types:

```graphql
type User @key(fields: "email") {
  id: ID!
  name: String
  email: String!
}
```

```graphql
type Review @key(fields: "id") {
  id: ID!
  body: String
}
```

```graphql
type Product @key(fields: "upc") {
  upc: String!
  name: String
  price: Int
  weight: Int
}
```

The next step is to connect together our types in the distributed architecture.

Let's extend types that are defined by another implementing service to illustrate the power of the federation. In our case, the reviews service extends the `User` and `Product` types by adding a reviews field to them:

```graphql
type Review @key(fields: "id") {
  id: ID!
  body: String
  author: User @provides(fields: "email")
  product: Product @provides(fields: "upc")
}

type User @key(fields: "email") @extends {
  email: String! @external
  reviews: [Review]
}

type Product @key(fields: "upc") @extends {
  upc: String! @external
  reviews: [Review]
}
```

Now our federated schemas are ready. It's time for resolvers.

We need to add `reference resolvers` for all our federated types. A reference resolver tells the gateway how to fetch an entity by its `@key` fields.

```python
# service_users.py
from ariadne.contrib.federation import FederatedObjectType


user = FederatedObjectType("User")

@user.reference_resolver
def resolve_user_reference(_, _info, representation):
    return get_user_by_email(representation.get("email"))
```

```python
# service_products.py
from ariadne.contrib.federation import FederatedObjectType


product = FederatedObjectType("Product")

@product.reference_resolver
def resolve_product_reference(_, _info, representation):
    return get_product_by_upc(representation["upc"])
```



```python
# service_reviews.py
from ariadne.contrib.federation import FederatedObjectType

type_defs = """
  type Query {
    reviews(first: Int = 5): [Review]
  }

  type Review @key(fields: "id") {
    id: ID!
    body: String
    author: User @provides(fields: "email")
    product: Product @provides(fields: "upc")
  }

  type User @key(fields: "email") @extends {
    email: String! @external
    reviews: [Review]
  }

  type Product @key(fields: "upc") @extends {
    upc: String! @external
    reviews: [Review]
  }
"""

review = FederatedObjectType("Review")
user = FederatedObjectType("User")
product = FederatedObjectType("Product")

@review.reference_resolver
def resolve_reviews_reference(_, _info, representation):
    return get_review_by_id(representation["id"])


@review.field("author")
def resolve_review_author(review, *_):
    return {"email": review["user"]["email"]}


@review.field("product")
def resolve_review_product(review, *_):
    return {"upc": review["product"]["upc"]}


@user.field("reviews")
def resolve_user_reviews(representation, *_):
    return get_user_reviews(representation["email"])


@product.field("reviews")
def resolve_product_reviews(representation, *_):
    return get_product_reviews(representation["upc"])

```

Finally, we need to use the `make_federated_schema` function in each of our services to augment the schema definition with federation support:

```python
import uvicorn
from ariadne.asgi import GraphQL
from ariadne.contrib.federation import make_federated_schema

from .myapp import type_defs, resolvers, port


schema = make_federated_schema(type_defs, resolvers)
application = GraphQL(schema)

if __name__ == "__main__":
    uvicorn.run(application, host="0.0.0.0", port=port)
```

### Federated Gateway

We need to set up a federated gateway that fetches the schema from each implementing service and composes those schemas into a single graph. We use [Apollo Gateway](https://www.apollographql.com/docs/apollo-server/federation/implementing/#running-a-gateway) for that.

```javascript
// gateway.js
const { ApolloServer } = require('apollo-server');
const { ApolloGateway } = require("@apollo/gateway");

const gateway = new ApolloGateway({
  serviceList: [
    { name: 'users', url: 'http://localhost:5001' },
    { name: 'reviews', url: 'http://localhost:5002' },
    { name: 'products', url: 'http://localhost:5003' },
  ],
});

const server = new ApolloServer({ gateway });

server.listen().then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});
```

### Example queries

Now it's time to verify our service and reap the benefits of federated architecture by executing GraphQL operations as if it were implemented as a monolithic service:

```graphql
query {
  me {
    name
    email
    reviews {
      body
      product {
        upc
        name
      }
    }
  }
  topProducts(first: 3) {
    upc
    name
    reviews {
      body
      author {
        name
        email
      }
    }
  }
}
```

Fully working demo is available on [GitHub](https://github.com/bogdal/ariadne-federation-demo).


## Creating new project from a template

Our friends from [Apollo Graph](https://apollographql.com/) have contributed and are maintaining a rover template for quickly starting with new GraphQL service with Ariadne and FastAPI that can be included in your federation.

This template can be found here: [mirumee/subgraph-template-ariadne-fastapi](https://github.com/mirumee/subgraph-template-ariadne-fastapi).
