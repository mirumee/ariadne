---
id: dataloaders
title: Dataloaders
---

Dataloaders are a GraphQL pattern for solving the N+1 problem, where retrieval of **N number of items** results in **N + 1 number of data retrieval operations**.


## The "N+1" problem

Let's take the GraphQL schema modeling a simple relation where messages have users who posted them:

```graphql
type Query {
    messages: [Message!]!
}

type Message {
    id: ID!
    message: String!
    poster: User
}

type User {
    id: ID!
    name: String!
}
```

Resolver for `messages` field selects messages from database ordered by their id in reverse order:

```python
def resolve_query_messages(*_):
    return db_fetch_all(
        "SELECT id, poster_id, message FROM messages ORDER BY id DESC"
    )
```

Resolver for `poster` field checks if message has id of a user who posted it, and if it does, retrieves this user from the database:

```python
def resolve_message_poster(message, *_):
    if not message["poster_id"]:
        return None  # Skip database query when message has no poster

    return db_fetch_one(
        "SELECT id, name FROM users WHERE id = %s", message["poster_id"]
    )
```

Assuming that there are **20 rows** in `messages` table in database, this GraphQL query will **cause 21 database queries**:

```graphql
query SelectMessages {
    messages {
        id
        message
        poster {
            id
            name
        }
    }
}
```

There's 1 database query for messages which returns 20 rows, each row causing one extra database query:

```sql
SELECT id, poster_id, message FROM messages ORDER BY id DESC;
SELECT id, name FROM users WHERE id = 39;
SELECT id, name FROM users WHERE id = 31;
SELECT id, name FROM users WHERE id = 39;
SELECT id, name FROM users WHERE id = 96;
SELECT id, name FROM users WHERE id = 19;
SELECT id, name FROM users WHERE id = 63;
SELECT id, name FROM users WHERE id = 32;
SELECT id, name FROM users WHERE id = 34;
SELECT id, name FROM users WHERE id = 48;
SELECT id, name FROM users WHERE id = 12;
SELECT id, name FROM users WHERE id = 12;
SELECT id, name FROM users WHERE id = 12;
SELECT id, name FROM users WHERE id = 41;
SELECT id, name FROM users WHERE id = 98;
SELECT id, name FROM users WHERE id = 19;
SELECT id, name FROM users WHERE id = 42;
SELECT id, name FROM users WHERE id = 46;
SELECT id, name FROM users WHERE id = 31;
SELECT id, name FROM users WHERE id = 48;
SELECT id, name FROM users WHERE id = 92;
```

20 rows is our `N`, and extra query is `+1`. This is the famous "N+1" problem in action.


## Half-measures

There are some solutions to this problem that can be implemented quickly, but have their own drawbacks.

For example, we can update `messages` resolver to use database `JOIN` operation, thus retrieving messages together with their posters:

```python
def resolve_query_messages(*_):
    return db_fetch_all(
        """
        SELECT m.id, m.poster_id, m.message, u.id AS u_id, u.name AS u_name
        FROM messages AS m
        LEFT JOIN users AS u ON m.poster_id = u.id;
        ORDER BY m.id DESC
        """
    )
```

Now we can update `poster` resolver to pull user's data from result:

```python
def resolve_message_poster(message, *_):
    if not message["u_id"]:
        return None  # Skip when message has no poster

    return {
        "id": message["u_id"],
        "name": message["u_name"],
    }
```

This change is enough to fix the issue. If we are using an ORM, it may not even require `resolve_message_poster` resolver to exist at all because `message` object will have `poster` attribute populated by the joined value.

**But** if GraphQL query doesn't include the `poster` field, we now potentially spend a lot of extra work and memory retrieving data we won't use. This is the overfetching problem that GraphQL is supposed to solve, even if this time its limited to server only.

What if instead of database we are using remote API? We will still need to run two API calls:

```python
def resolve_query_messages(*_):
    messages = client.get("http://api.example.com/messages/")

    posters = {
        message["poster_id"]: None
        for message in messages if message["poster_id"]
    }

    if posters:
        api_qs = "&".join(f"id={uid}" for uid in posters)
        api_url = f"http://api.example.com/users/?{api_qs}"

        for poster in client.get(api_url):
            posters[poster["id"]] = poster

        for message in messages:
            message["poster"] = posters.get(message["poster_id"])

    return messages
```

There's quite a lot of extra logic. What if there are more lists of items that have relation to `user`? Most likely we will now have an util for our resolvers to fetch their users:

```python
def get_users_from_api(users_ids: list[int]) -> dict[int, dict]:
    if not users_ids:
        return {}

    api_values = "&".join(f"id={uid}" for uid in users_ids)
    api_url = f"http://api.example.com/users/?{api_values}"

    return {user["id"]: user for user in client.get(api_url)}
```

We are now a **half**-way to implementing a dataloader. 👏


## Dataloader

Dataloader is a proxy to a data source. What this data source is doesn't matter. For performance reasons its important that this source supports bulk retrieval of items, but thats not required.

Dataloader **knows** how to retrieve required objects in most optimal way.

Dataloader **batches** multiple retrieval operations into one.

Dataloader **may** cache retrieved items to make repeated retrievals faster.

In short, dataloader is **magic**:

```python
def load_user(user_id: int) -> Optional[dict]:
    # 🌟 magic 🌟


def resolve_message_poster(message, *_):
    if not message["poster_id"]:
        return None  # Skip when message has no poster

    return load_user(message["poster_id"])
```


## Async dataloader

If you are using `async` approach (eg. `ariadne.graphql` or `ariadne.asgi.GraphQL`), use [`aiodataloader`](https://github.com/syrusakbary/aiodataloader):

```
$ pip install aiodataloader
```


### Loader function

After installing `aiodataloader`, we will need to first define function it will use to load data. 

`aiodataloader` requires those functions to take single argument (list of IDs of objects to retrieve), and return a list with retrieved objects, in the order of ids it was called with, with items that couldn't be found represented as `None`.

In this example we will continue using the `get_users_from_api` function, but we need to make some changes to it first.

```python
from httpx import AsyncClient

async def get_users_from_api(users_ids: list[int]) -> list[dict]:
    # Build API URL
    api_values = "&".join(f"id={uid}" for uid in users_ids)
    api_url = f"http://api.example.com/users/?{api_values}"

    # Fetch users from API
    async with AsyncClient() as client:
        ids_map = {user["id"]: user for user in await client.get(api_url)}

    # Return user as list using same order as users_ids passed to function
    # Replace result with none when user with given id was not returned
    return [ids_map.get(uid) for uid in users_ids]
```


### Initializing loader in context

We now need to store instance of `aiodataloader.DataLoader` with our function in a place that's bound to HTTP request but also accessible by our GraphQL resolvers. GraphQL `context` was created exactly for this case:

```python
from aiodataloader import DataLoader
from ariadne.asgi import GraphQL
from httpx import AsyncClient
from starlette.requests import Request

from .schema import schema


async def get_users_from_api(users_ids: list[int]) -> list[dict]:
    # Build API URL
    api_values = "&".join(f"id={uid}" for uid in users_ids)
    api_url = f"http://api.example.com/users/?{api_values}"

    # Fetch users from API
    async with AsyncClient() as client:
        ids_map = {user["id"]: user for user in await client.get(api_url)}

    # Return user as list using same order as users_ids passed to function
    # Replace result with none when user with given id was not returned
    return [ids_map.get(uid) for uid in users_ids]


def get_context_value(request: Request, data: dict):
    # Context value function will be called for every request to GraphQL server
    # Its retrievable as `context` attribute of resolver's second argument
    return {
        "request": request,
        "user_loader": DataLoader(get_users_from_api)
    }

asgi_app = GraphQL(schema, context_value=get_context_value)
```


### Using loader in resolvers

We can now update our `poster` resolver to use the loader:

```python
def resolve_message_poster(message, info):
    if not message["u_id"]:
        return None  # Skip when message has no poster

    return info.context["user_loader"].load(message["u_id"])
```

`DataLoader.load()` takes id of an object to load, and returns awaitable for this object or `None` (when it could not be loaded). GraphQL resolvers can be `async`, but can also just return awaitable values. Below resolver behaves the same as previous one during GraphQL query execution:

```python
async def resolve_message_poster(message, info):
    if not message["u_id"]:
        return None  # Skip when message has no poster

    return await info.context["user_loader"].load(message["u_id"])
```

It doesn't matter which approach you use, but if you want to do something with loaded value before returning it from resolver, you will need `async` resolver that awaits it before returning it:

```python
async def resolve_message_poster(message, info):
    if not message["u_id"]:
        return None  # Skip when message has no poster

    user = await info.context["user_loader"].load(message["u_id"])

    # Test if loaded user was banned and don't return them if so
    if not user or user.is_banned:
        return None

    return user
```


### Cache

`DataLoader` caches previously loaded objects on it's instance, so repeated calls to `load` previously loaded objects don't trigger new loads.

This cache can become stale in situations when mutation resolver changes application state. If this happens you can manually remove the object from cache using `clear(key)` method, or clear entire cache with `clear_all` method:

```python
async def resolve_move_category_contents(_, info, **kwargs):
    # ... logic doing something with category

    # Remove category from categories dataloder
    info.context["categories_loader"].clear(category.id)

    # Clear threads and posts dataloaders cache because their category_id
    # attributes are no longer valid and can cause problem in other resolvers
    info.context["thread_loader"].clear_all()
    info.context["post_loader"].clear_all()

    return {"success": True}
```

You can also put object in the cache without loading it using `prime` method:

```python
async def resolve_register_user_account(_, info, **kwargs):
    # ... logic validating and registering `user` account

    # Store user in dataloader in case it will be used by other resolvers
    # during this GraphQL query
    info.context["user_loader"].prime(user.id, user)

    return {"user": user}
```

Initialize the `DataLoader` with `cache=False` to disable caching:

```python
def get_context_value(request: Request, data: dict):
    # Context value function will be called for every request to GraphQL server
    # Its retrievable as `context` attribute of resolver's second argument
    return {
        "request": request,
        "user_loader": DataLoader(get_users_from_api, cache=False)
    }
```


## Sync dataloader

If you are using sync approach, use [`graphql-sync-dataloaders`](https://github.com/jkimbo/graphql-sync-dataloaders) (Python 3.8 and later only):

```
$ pip install graphql-sync-dataloaders
```

### Loader function

After installing `graphql-sync-dataloaders`, we will need to first define function it will use to load data. 

`graphql-sync-dataloaders` requires those functions to take single argument (list of IDs of objects to retrieve), and return a list with retrieved objects, in the order of ids it was called with, with items that couldn't be found represented as `None`.

In this example we will continue using the `get_users_from_api` function, but we need to make some changes to it first.

```python
import httpx

def get_users_from_api(users_ids: list[int]) -> list[dict]:
    # Build API URL
    api_values = "&".join(f"id={uid}" for uid in users_ids)
    api_url = f"http://api.example.com/users/?{api_values}"

    # Fetch users from API
    ids_map = {user["id"]: user for user in httpx.get(api_url)}

    # Return user as list using same order as users_ids passed to function
    # Replace result with none when user with given id was not returned
    return [ids_map.get(uid) for uid in users_ids]
```


### Initializing loader in context

We now need to store instance of `graphql_sync_dataloaders.SyncDataLoader` with our function in a place that's bound to HTTP request but also accessible by our GraphQL resolvers. We will use GraphQL `context` for this case, but we also need to set custom `DeferredExecutionContext` GraphQL execution context class which knows about our dataloader.

Here's example Flask application:

```python
import requests
from graphql_sync_dataloaders import DeferredExecutionContext, SyncDataLoader
from ariadne import graphql_sync
from flask import Flask, jsonify, request

from .schema import schema


def get_users_from_api(users_ids: list[int]) -> list[dict]:
    # Build API URL
    api_values = "&".join(f"id={uid}" for uid in users_ids)
    api_url = f"http://api.example.com/users/?{api_values}"

    # Fetch users from API
    ids_map = {user["id"]: user for user in httpx.get(api_url)}

    # Return user as list using same order as users_ids passed to function
    # Replace result with none when user with given id was not returned
    return [ids_map.get(uid) for uid in users_ids]


app = Flask(__name__)


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()

    success, result = graphql_sync(
        schema,
        data,
        # Context value with dataloader available as `user_loader`
        context_value={
            "request": request,
            "user_loader": SyncDataLoader(get_users_from_api),
        },
        # Use DeferredExecutionContext as custom execution context
        execution_context_class=DeferredExecutionContext,
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    app.run(debug=True)
```


### Using loader in resolvers

We can now update our `poster` resolver to use the loader:

```python
def resolve_message_poster(message, info):
    if not message["u_id"]:
        return None  # Skip when message has no poster

    return info.context["user_loader"].load(message["u_id"])
```

`SyncDataLoader.load()` takes id of an object to load, and returns `SyncFuture` for this object or `None` (when it could not be loaded). `DeferredExecutionContext` then knows how to gather `SyncFuture` returned by multiple resolver calls, then batch load and replace them with their results.

If you want to do something with loaded object before returning it, you need to do it in a callback passed to it with `then` method:

```python
def resolve_message_poster(message, info):
    if not message["u_id"]:
        return None  # Skip when message has no poster

    def return_user_if_not_banned(user):
        if not user or user.is_banned:
            return None

        return user

    return info.context["user_loader"].load(
        message["u_id"]
    ).then(
        return_user_if_not_banned
    )
```


### Cache

`SyncDataLoader` caches previously loaded objects on it's instance, so repeated calls to `load` previously loaded objects don't trigger new loads.

This cache can become stale in situations when mutation resolver changes application state. If this happens you can manually remove the object from cache using `clear(key)`:

```python
async def resolve_move_category_contents(_, info, **kwargs):
    # ... logic doing something with category

    # Remove category from categories dataloder
    info.context["categories_loader"].clear(category.id)

    return {"success": True}
```

Unlike `DataLoader`, `SyncDataLoader` doesn't provide an API for clearing entire cache or priming objects.