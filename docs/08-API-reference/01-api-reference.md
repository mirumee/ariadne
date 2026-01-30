---
id: api-reference
title: API reference
sidebar_label: ariadne
---

Following items are importable directly from `ariadne` package:


## `EnumType`

```python
class EnumType(SchemaBindable):
    ...
```

[Bindable](../Docs/bindables) mapping Python values to enumeration members in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).


### Constructor

```python
def __init__(
    self,
    name: str,
    values: Union[Dict[str, Any], Type[enum.Enum], Type[enum.IntEnum]],
):
    ...
```

Initializes the `EnumType` with `name` and `values` mapping.


#### Required arguments

`name`: a `str` with the name of GraphQL enum type in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind to.

`values`: a `dict` or `enums.Enum` with values to use to represent GraphQL
enum's in Python logic.


### Methods

#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `EnumType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).


#### `bind_to_default_values`

```python
def bind_to_default_values(self, _schema: GraphQLSchema) -> None:
    ...
```

Populates default values of input fields and args in the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

This step is required because GraphQL query executor doesn't perform a
lookup for default values defined in schema. Instead it simply pulls the
value from fields and arguments `default_value` attribute, which is
`None` by default.

> **Deprecated:** Ariadne versions before 0.22 used
`EnumType.bind_to_default_values` method to fix default enum values embedded
in the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema). Ariadne 0.22 release introduces universal
`repair_schema_default_enum_values` utility in its place.


#### `validate_graphql_type`

```python
def validate_graphql_type(
    self,
    graphql_type: Optional[GraphQLNamedType],
) -> None:
    ...
```

Validates that schema's GraphQL type associated with this `EnumType`
is an `enum`.


### Example

Given following GraphQL enum:

```graphql
enum UserRole {
    MEMBER
    MODERATOR
    ADMIN
}
```

You can use `EnumType` to map it's members to Python `Enum`:

```python
user_role_type = EnumType(
    "UserRole",
    {
        "MEMBER": 0,
        "MODERATOR": 1,
        "ADMIN": 2,
    }
)
```

`EnumType` also works with dictionaries:

```python
user_role_type = EnumType(
    "UserRole",
    {
        "MEMBER": 0,
        "MODERATOR": 1,
        "ADMIN": 2,
    }
)
```


- - - - -


## `Extension`

```python
class Extension:
    ...
```

Base class for extensions.

Subclasses of this class should override default methods to run
custom logic during Query execution.


### Methods

#### `request_started`

```python
def request_started(self, context: ContextValue) -> None:
    ...
```

Extension hook executed at request's start.


#### `request_finished`

```python
def request_finished(self, context: ContextValue) -> None:
    ...
```

Extension hook executed at request's end.


#### `resolve`

```python
def resolve(
    self,
    next_: Resolver,
    obj: Any,
    info: GraphQLResolveInfo,
    **kwargs,
) -> Any:
    ...
```

Extension hook wrapping field's value resolution.


##### Arguments

`next_`: a `resolver` or next extension's `resolve` method.

`obj`: a Python data structure to resolve value from.

`info`: a `GraphQLResolveInfo` instance for executed resolver.

`**kwargs`: extra arguments from GraphQL to pass to resolver.


##### Example

`resolve` should handle both sync and async `next_`:

```python
from inspect import iscoroutinefunction
from time import time

from ariadne.types import Extension, Resolver
from graphql import GraphQLResolveInfo
from graphql.pyutils import is_awaitable

class MyExtension(Extension):
    def __init__(self):
        self.paths = []

    def resolve(
        self, next_: Resolver, obj: Any, info: GraphQLResolveInfo, **kwargs
    ) -> Any:
        path = ".".join(map(str, info.path.as_list()))

        # Fast implementation for synchronous resolvers
        if not iscoroutinefunction(next_):
            start_time = time()
            result = next_(obj, info, **kwargs)
            self.paths.append((path, time() - start_time))
            return result

        # Create async closure for async `next_` that GraphQL
        # query executor will handle for us.
        async def async_my_extension():
            start_time = time()
            result = await next_(obj, info, **kwargs)
            if is_awaitable(result):
                result = await result
            self.paths.append((path, time() - start_time))
            return result

        # GraphQL query executor will execute this closure for us
        return async_my_extension()
```


#### `has_errors`

```python
def has_errors(
    self,
    errors: List[GraphQLError],
    context: ContextValue,
) -> None:
    ...
```

Extension hook executed when GraphQL encountered errors.


#### `format`

```python
def format(self, context: ContextValue) -> Optional[dict]:
    ...
```

Extension hook executed to retrieve extra data to include in result's
[`extensions`](types-reference#extensions) data.


- - - - -


## `ExtensionManager`

```python
class ExtensionManager:
    ...
```

Container and runner for extensions and middleware, used by the GraphQL servers.


### Attributes

`context`: the [`ContextValue`](types-reference#contextvalue) of type specific to the server.

[`extensions`](types-reference#extensions): a `tuple` with instances of initialized extensions.

`extensions_reversed`: a `tuple` created from reversing [`extensions`](types-reference#extensions).


### Constructor

```python
def __init__(
    self,
    extensions: Optional[ExtensionList] = None,
    context: Optional[ContextValue] = None,
):
    ...
```

Initializes extensions and stores them with context on instance.


#### Optional arguments

[`extensions`](types-reference#extensions): a `list` of `Extension` types to initialize.

`context`: the [`ContextValue`](types-reference#contextvalue) of type specific to the server.


### Methods

#### `as_middleware_manager`

```python
def as_middleware_manager(
    self,
    middleware: MiddlewareList = None,
    manager_class: Optional[Type[MiddlewareManager]] = None,
) -> Optional[MiddlewareManager]:
    ...
```

Creates middleware manager instance combining middleware and extensions.

Returns instance of the type passed in `manager_class` argument
or `MiddlewareManager` that query executor then uses.


##### Optional arguments

`middleware`: a `list` of `Middleware` instances

`manager_class` a `type` of middleware manager to use. `MiddlewareManager`
is used if this argument is passed `None` or omitted.


#### `request`

```python
def request(self) -> None:
    ...
```

A context manager that should wrap request processing.

Runs `request_started` hook at beginning and `request_finished` at
the end of request processing, enabling APM extensions like ApolloTracing.


#### `has_errors`

```python
def has_errors(self, errors: List[GraphQLError]) -> None:
    ...
```

Propagates GraphQL errors returned by GraphQL server to extensions.

Should be called only when there are errors.


#### `format`

```python
def format(self) -> dict:
    ...
```

Gathers data from extensions for inclusion in server's response JSON.

This data can be retrieved from the [`extensions`](types-reference#extensions) key in response JSON.

Returns `dict` with JSON-serializable data.


- - - - -


## `FallbackResolversSetter`

```python
class FallbackResolversSetter(SchemaBindable):
    ...
```

[Bindable](../Docs/bindables) that recursively scans [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) for fields and explicitly
sets their resolver to `graphql.default_field_resolver` package if
they don't have any resolver set yet.

> **Deprecated:** This class doesn't provide any utility for developers and
only serves as a base for `SnakeCaseFallbackResolversSetter` which is being
replaced by what we believe to be a better solution.
>
> Because of this we are deprecating this utility. It will be removed in future
Ariadne release.


### Methods

#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Scans [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) for types with fields that don't have set resolver.


#### `add_resolvers_to_object_fields`

```python
def add_resolvers_to_object_fields(
    self,
    type_object: GraphQLObjectType,
) -> None:
    ...
```

Sets explicit default resolver on a fields of an object that don't have any.


#### `add_resolver_to_field`

```python
def add_resolver_to_field(self, _: str, field_object: GraphQLField) -> None:
    ...
```

Sets `default_field_resolver` as a resolver on a field that doesn't have any.


- - - - -


## `InputType`

```python
class InputType(SchemaBindable):
    ...
```

[Bindable](../Docs/bindables) populating input types in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic.


### Constructor

```python
def __init__(
    self,
    name: str,
    out_type: Optional[GraphQLInputFieldOutType] = None,
    out_names: Optional[Dict[str, str]] = None,
):
    ...
```

Initializes the `InputType` with a `name` and optionally out type
and out names.


#### Required arguments

`name`: a `str` with the name of GraphQL object type in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind to.


#### Optional arguments

`out_type`: a `GraphQLInputFieldOutType`, Python callable accepting single
argument, a dict with data from GraphQL query, required to return
a Python representation of input type.

`out_names`: a `Dict[str, str]` with mappings from GraphQL field names
to dict keys in a Python dictionary used to contain a data passed as
input.


### Methods

#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `InputType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

if it has an out type function, it assigns it to GraphQL type's
`out_type` attribute. If type already has other function set on
it's `out_type` attribute, this type is replaced with new one.

If it has any out names set, it assigns those to GraphQL type's
fields `out_name` attributes. If field already has other out name set on
its `out_name` attribute, this name is replaced with the new one.


#### `validate_graphql_type`

```python
def validate_graphql_type(
    self,
    graphql_type: Optional[GraphQLNamedType],
) -> None:
    ...
```

Validates that schema's GraphQL type associated with this `InputType`
is an `input`.


### Example input value represented as dataclass

Following code creates a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with object type named `Query`
with single field which has an argument of an input type. It then uses
the `InputType` to set `ExampleInput` dataclass as Python representation
of this GraphQL type:

```python
from dataclasses import dataclass

from ariadne import InputType, QueryType, make_executable_schema

@dataclass
class ExampleInput:
    id: str
    message: str

query_type = QueryType()

@query_type.field("repr")
def resolve_repr(*_, input: ExampleInput):
    return repr(input)

schema = make_executable_schema(
    """
    type Query {
        repr(input: ExampleInput): String!
    }

    input ExampleInput {
        id: ID!
        message: String!
    }
    """,
    query_type,
    # Lambda is used because out type (second argument of InputType)
    # is called with single dict and dataclass requires each value as
    # separate argument.
    InputType("ExampleInput", lambda data: ExampleInput(**data)),
)
```


### Example input with its fields mapped to custom dict keys

Following code creates a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with object type named `Query`
with single field which has an argument of an input type. It then uses
the `InputType` to set custom "out names" values, mapping GraphQL
`shortMessage` to `message` key in Python dict:

```python
from ariadne import InputType, QueryType, make_executable_schema

query_type = QueryType()

@query_type.field("repr")
def resolve_repr(*_, input: dict):
    # Dict will have `id` and `message` keys
    input_id = input["id"]
    input_message = input["message"]
    return f"id: {input_id}, message: {input_message}"

schema = make_executable_schema(
    """
    type Query {
        repr(input: ExampleInput): String!
    }

    input ExampleInput {
        id: ID!
        shortMessage: String!
    }
    """,
    query_type,
    InputType("ExampleInput", out_names={"shortMessage": "message"}),
)
```


### Example input value as dataclass with custom named fields

Following code creates a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with object type named `Query`
with single field which has an argument of an input type. It then uses
the `InputType` to set `ExampleInput` dataclass as Python representation
of this GraphQL type, and maps `shortMessage` input field to it's
`message` attribute:

```python
from dataclasses import dataclass

from ariadne import InputType, QueryType, make_executable_schema

@dataclass
class ExampleInput:
    id: str
    message: str

query_type = QueryType()

@query_type.field("repr")
def resolve_repr(*_, input: ExampleInput):
    return repr(input)

schema = make_executable_schema(
    """
    type Query {
        repr(input: ExampleInput): String!
    }

    input ExampleInput {
        id: ID!
        shortMessage: String!
    }
    """,
    query_type,
    InputType(
        "ExampleInput",
        lambda data: ExampleInput(**data),
        {"shortMessage": "message"},
    ),
)
```


- - - - -


## `InterfaceType`

```python
class InterfaceType(ObjectType):
    ...
```

[Bindable](../Docs/bindables) populating interfaces in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic.

Extends `ObjectType`, providing `field` decorator and `set_field` and `set_alias`
methods. If those are used to set resolvers for interface's fields, those
resolvers will instead be set on fields of GraphQL types implementing this
interface, but only if those fields don't already have resolver of their own set
by the `ObjectType`.


### Type resolver

Because GraphQL fields using interface as their returning type can return any
Python value from their resolver, GraphQL interfaces require special type of
resolver called "type resolver" to function.

This resolver is called with the value returned by field's resolver and is
required to return a string with a name of GraphQL type represented by Python
value from the field:

```python
def example_type_resolver(obj: Any, *_) -> str:
    if isinstance(obj, PythonReprOfUser):
        return "User"

    if isinstance(obj, PythonReprOfComment):
        return "Comment"

    raise ValueError(f"Don't know GraphQL type for '{obj}'!")
```

This resolver is not required if the GraphQL field returns a value that has
the `__typename` attribute or `dict` key with a name of the GraphQL type:

```python
user_data_dict = {"__typename": "User", ...}

# or...

class UserRepr:
    __typename: str = "User"
```


### Constructor

```python
def __init__(
    self,
    name: str,
    type_resolver: Optional[Resolver] = None,
):
    ...
```

Initializes the `InterfaceType` with a `name` and optional `type_resolver`.

Type resolver is required by `InterfaceType` to function properly, but can
be set later using either `set_type_resolver(type_resolver)`
setter or `type_resolver` decorator.


#### Required arguments

`name`: a `str` with the name of GraphQL interface type in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind to.


#### Optional arguments

`type_resolver`: a `Resolver` used to resolve a str with name of GraphQL type
from it's Python representation.


### Methods

#### `set_type_resolver`

```python
def set_type_resolver(self, type_resolver: Resolver) -> Resolver:
    ...
```

Sets function as type resolver for this interface.

Can be used as a decorator. Also available through `type_resolver` alias:

```python
interface_type = InterfaceType("MyInterface")

@interface_type.type_resolver
def type_resolver(obj: Any, *_) -> str:
    ...
```


#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `InterfaceType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

Sets `resolve_type` attribute on GraphQL interface. If this attribute was
previously set, it will be replaced to new value.

If this interface has any resolvers set, it also scans [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) for
types implementing this interface and sets those resolvers on those types
fields, but only if those fields don't already have other resolver set.


#### `validate_graphql_type`

```python
def validate_graphql_type(
    self,
    graphql_type: Optional[GraphQLNamedType],
) -> None:
    ...
```

Validates that schema's GraphQL type associated with this `InterfaceType`
is an `interface`.


### Example

Following code creates a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with a field that returns random
result of either `User` or `Post` GraphQL type. It also supports dict with
`__typename` key that explicitly declares its GraphQL type:

```python
import random
from dataclasses import dataclass
from ariadne import QueryType, InterfaceType, make_executable_schema

@dataclass
class UserModel:
    id: str
    name: str

@dataclass
class PostModel:
    id: str
    message: str

results = (
    UserModel(id=1, name="Bob"),
    UserModel(id=2, name="Alice"),
    UserModel(id=3, name="Jon"),
    PostModel(id=1, message="Hello world!"),
    PostModel(id=2, message="How's going?"),
    PostModel(id=3, message="Sure thing!"),
    {"__typename": "User", "id": 4, "name": "Polito"},
    {"__typename": "User", "id": 5, "name": "Aerith"},
    {"__typename": "Post", "id": 4, "message": "Good day!"},
    {"__typename": "Post", "id": 5, "message": "Whats up?"},
)

query_type = QueryType()

@query_type.field("result")
def resolve_random_result(*_):
    return random.choice(results)


result_type = InterfaceType("Result")

@result_type.type_resolver
def resolve_result_type(obj: UserModel | PostModel | dict, *_) -> str:
    if isinstance(obj, UserModel):
        return "User"

    if isinstance(obj, PostModel):
        return "Post"

    if isinstance(obj, dict) and obj.get("__typename"):
        return obj["__typename"]

    raise ValueError(f"Don't know GraphQL type for '{obj}'!")


schema = make_executable_schema(
    """
    type Query {
        result: Result!
    }

    interface Result {
        id: ID!
    }

    type User implements Result {
        id: ID!
        name: String!
    }

    type Post implements Result {
        id: ID!
        message: String!
    }
    """,
    query_type,
    result_type,
)
```


- - - - -


## `MutationType`

```python
class MutationType(ObjectType):
    ...
```

An convenience class for defining Mutation type.


### Constructor

```python
def __init__(self):
    ...
```

Initializes the `MutationType` with a GraphQL name set to `Mutation`.


### Example

Both of those code samples have same result:

```python
mutation_type = MutationType()
```

```python
mutation_type = ObjectType("Mutation")
```


- - - - -


## `ObjectType`

```python
class ObjectType(SchemaBindable):
    ...
```

[Bindable](../Docs/bindables) populating object types in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic.


### Constructor

```python
def __init__(self, name: str):
    ...
```

Initializes the `ObjectType` with a `name`.


#### Required arguments

`name`: a `str` with the name of GraphQL object type in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind to.


### Methods

#### `field`

```python
def field(self, name: str) -> Callable[[Resolver], Resolver]:
    ...
```

Return a decorator that sets decorated function as a resolver for named field.

Wrapper for `create_register_resolver` that on runtime validates `name` to be a
string.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind decorated resolver to.


#### `create_register_resolver`

```python
def create_register_resolver(
    self,
    name: str,
) -> Callable[[Resolver], Resolver]:
    ...
```

Return a decorator that sets decorated function as a resolver for named field.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind decorated resolver to.


#### `set_field`

```python
def set_field(self, name, resolver: Resolver) -> Resolver:
    ...
```

Set a resolver for the field name.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
set this resolver for.

`resolver`: a `Resolver` function to use.


#### `set_alias`

```python
def set_alias(self, name: str, to: str) -> None:
    ...
```

Set an alias resolver for the field name to given Python name.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
set this resolver for.

`to`: a `str` of an attribute or dict key to resolve this field to.


#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `ObjectType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

If it has any resolver functions set, it assigns those to GraphQL type's
fields `resolve` attributes. If field already has other resolver set on
its `resolve` attribute, this resolver is replaced with the new one.


#### `validate_graphql_type`

```python
def validate_graphql_type(
    self,
    graphql_type: Optional[GraphQLNamedType],
) -> None:
    ...
```

Validates that schema's GraphQL type associated with this `ObjectType`
is a `type`.


#### `bind_resolvers_to_graphql_type`

```python
def bind_resolvers_to_graphql_type(
    self,
    graphql_type,
    replace_existing = True,
) -> None:
    ...
```

Binds this `ObjectType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).


### Example

Following code creates a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with single object type named `Query`
and uses `ObjectType` to set resolvers on its fields:

```python
import random
from datetime import datetime

from ariadne import ObjectType, make_executable_schema

query_type = ObjectType("Query")

@query_type.field("diceRoll")
def resolve_dice_roll(*_):
    return random.int(1, 6)


@query_type.field("year")
def resolve_year(*_):
    return datetime.today().year


schema = make_executable_schema(
    """
    type Query {
        diceRoll: Int!
        year: Int!
    }
    """,
    query_type,
)
```


### Example with objects in objects

When a field in the schema returns other GraphQL object, this object's
resolvers are called with value returned from field's resolver. For example
if there's an `user` field on the `Query` type that returns the `User` type,
you don't have to resolve `User` fields in `user` resolver. In below example
`fullName` field on `User` type is resolved from data on `UserModel` object
that `user` field resolver on `Query` type returned:

```python
import dataclasses
from ariadne import ObjectType, make_executable_schema

@dataclasses.dataclass
class UserModel:
    id: int
    username: str
    first_name: str
    last_name: str


users = [
    UserModel(
        id=1,
        username="Dany",
        first_name="Daenerys",
        last_name="Targaryen",
    ),
    UserModel(
        id=2,
        username="BlackKnight19",
        first_name="Cahir",
        last_name="Mawr Dyffryn aep Ceallach",
    ),
    UserModel(
        id=3,
        username="TheLady",
        first_name="Dorotea",
        last_name="Senjak",
    ),
]


# Query type resolvers return users, but don't care about fields
# of User type
query_type = ObjectType("Query")

@query_type.field("users")
def resolve_users(*_) -> list[UserModel]:
    # In real world applications this would be a database query
    # returning iterable with user results
    return users


@query_type.field("user")
def resolve_user(*_, id: str) -> UserModel | None:
    # In real world applications this would be a database query
    # returning single user or None

    try:
        # GraphQL ids are always strings
        clean_id = int(id)
    except (ValueError, TypeError):
        # We could raise "ValueError" instead
        return None

    for user in users:
        if user.id == id:
            return user

    return None


# User type resolvers don't know how to retrieve User, but know how to
# resolve User type fields from UserModel instance
user_type = ObjectType("User")

# Resolve "name" GraphQL field to "username" attribute
user_type.set_alias("name", "username")

# Resolve "fullName" field to combined first and last name
# `obj` argument will be populated by GraphQL with a value from
# resolver for field returning "User" type
@user_type.field("fullName")
def resolve_user_full_name(obj: UserModel, *_):
    return f"{obj.first_name} {obj.last_name}"


schema = make_executable_schema(
    """
    type Query {
        users: [User!]!
        user(id: ID!): User
    }

    type User {
        id: ID!
        name: String!
        fullName: String!
    }
    """,
    query_type,
    user_type,
)
```


- - - - -


## `QueryType`

```python
class QueryType(ObjectType):
    ...
```

An convenience class for defining Query type.


### Constructor

```python
def __init__(self):
    ...
```

Initializes the `QueryType` with a GraphQL name set to `Query`.


### Example

Both of those code samples have same effect:

```python
query_type = QueryType()
```

```python
query_type = ObjectType("Query")
```


- - - - -


## `ScalarType`

```python
class ScalarType(SchemaBindable):
    ...
```

[Bindable](../Docs/bindables) populating scalars in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic.

GraphQL scalars implement default serialization and deserialization logic.
This class is only useful when custom logic is needed, most commonly
when Python representation of scalar's value is not JSON-serializable by
default.

This logic can be customized for three steps:


### Serialization

Serialization step converts Python representation of scalar's value to a
JSON serializable format.

Serializer function takes single argument and returns a single,
JSON serializable value:

```python
def serialize_date(value: date) -> str:
    # Serialize dates as "YYYY-MM-DD" string
    return date.strftime("%Y-%m-%d")
```


### Value parsing

Value parsing step converts value from deserialized JSON
to Python representation.

Value parser function takes single argument and returns a single value:

```python
def parse_date_str(value: str) -> date:
    try:
        # Parse "YYYY-MM-DD" string into date
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f'"{value}" is not a date string in YYYY-MM-DD format.'
        )
```


### Literal parsing

Literal parsing step converts value from GraphQL abstract syntax tree (AST)
to Python representation.

Literal parser function takes two arguments, an AST node and a dict with
query's variables and returns Python value:

```python
def parse_date_literal(
    value: str, variable_values: dict[str, Any] = None
) -> date:
    if not isinstance(ast, StringValueNode):
        raise ValueError()

    try:
        # Parse "YYYY-MM-DD" string into date
        return datetime.strptime(ast.value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f'"{value}" is not a date string in YYYY-MM-DD format.'
        )
```

When scalar has custom value parser set, but not the literal parser, the
GraphQL query executor will use default literal parser, and then call the
value parser with it's return value. This mechanism makes custom literal
parser unnecessary for majority of scalar implementations.

Scalar literals are always parsed twice: on query validation and during
query execution.


### Constructor

```python
def __init__(
    self,
    name: str,
    *,
    serializer: Optional[GraphQLScalarSerializer],
    value_parser: Optional[GraphQLScalarValueParser],
    literal_parser: Optional[GraphQLScalarLiteralParser],
):
    ...
```

Initializes the `ScalarType` with a `name`.


#### Required arguments

`name`: a `str` with the name of GraphQL scalar in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind to.


#### Optional arguments

`serializer`: a function called to convert Python representation of
scalar's value to JSON serializable format.

`value_parser`: a function called to convert a JSON deserialized value
from query's "variables" JSON into scalar's Python representation.

`literal_parser`: a function called to convert an AST value
from parsed query into scalar's Python representation.


### Methods

#### `set_serializer`

```python
def set_serializer(
    self,
    f: GraphQLScalarSerializer,
) -> GraphQLScalarSerializer:
    ...
```

Sets function as serializer for this scalar.

Can be used as a decorator. Also available through `serializer` alias:

```python
date_scalar = ScalarType("Date")

@date_scalar.serializer
def serialize_date(value: date) -> str:
    # Serialize dates as "YYYY-MM-DD" string
    return date.strftime("%Y-%m-%d")
```


#### `set_value_parser`

```python
def set_value_parser(
    self,
    f: GraphQLScalarValueParser,
) -> GraphQLScalarValueParser:
    ...
```

Sets function as value parser for this scalar.

Can be used as a decorator. Also available through `value_parser` alias:

```python
date_scalar = ScalarType("Date")

@date_scalar.value_parser
def parse_date_str(value: str) -> date:
    try:
        # Parse "YYYY-MM-DD" string into date
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f'"{value}" is not a date string in YYYY-MM-DD format.'
        )
```


#### `set_literal_parser`

```python
def set_literal_parser(
    self,
    f: GraphQLScalarLiteralParser,
) -> GraphQLScalarLiteralParser:
    ...
```

Sets function as literal parser for this scalar.

Can be used as a decorator. Also available through `literal_parser` alias:

```python
date_scalar = ScalarType("Date")

@date_scalar.literal_parser
def parse_date_literal(
    value: str, variable_values: Optional[dict[str, Any]] = None
) -> date:
    if not isinstance(ast, StringValueNode):
        raise ValueError()

    try:
        # Parse "YYYY-MM-DD" string into date
        return datetime.strptime(ast.value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f'"{value}" is not a date string in YYYY-MM-DD format.'
        )
```


#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `ScalarType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

If it has serializer or parser functions set, it assigns those to GraphQL
scalar's attributes. If scalar's attribute already has other function
set, this function is replaced with the new one.


#### `validate_graphql_type`

```python
def validate_graphql_type(
    self,
    graphql_type: Optional[GraphQLNamedType],
) -> None:
    ...
```

Validates that schema's GraphQL type associated with this `ScalarType`
is a `scalar`.


### Example datetime scalar

Following code defines a datetime scalar which converts Python datetime
object to and from a string. Note that it without custom literal scalar:

```python
from datetime import datetime

from ariadne import QueryType, ScalarType, make_executable_schema

scalar_type = ScalarType("DateTime")

@scalar_type.serializer
def serialize_value(val: datetime) -> str:
    return datetime.strftime(val, "%Y-%m-%d %H:%M:%S")


@scalar_type.value_parser
def parse_value(val) -> datetime:
    if not isinstance(val, str):
        raise ValueError(
            f"'{val}' is not a valid JSON representation "
        )

    return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")


query_type = QueryType()

@query_type.field("now")
def resolve_now(*_):
    return datetime.now()


@query_type.field("diff")
def resolve_diff(*_, value):
    delta = datetime.now() - value
    return int(delta.total_seconds())


schema = make_executable_schema(
    """
    scalar DateTime

    type Query {
        now: DateTime!
        diff(value: DateTime): Int!
    }
    """,
    scalar_type,
    query_type,
)
```


### Example generic scalar

Generic scalar is a pass-through scalar that doesn't perform any value
conversion. Most common use case for those is for GraphQL fields that
return unstructured JSON to the client. To create a scalar like this,
you can simply include  `scalar Generic` in your [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema):

```python
from ariadne import QueryType, make_executable_schema

query_type = QueryType()

@query_type.field("rawJSON")
def resolve_raw_json(*_):
    # Note: this value needs to be JSON serializable
    return {
        "map": {
            "0": "Hello!",
            "1": "World!",
        },
        "list": [
            2,
            1,
            3,
            7,
        ],
    }


schema = make_executable_schema(
    """
    scalar Generic

    type Query {
        rawJSON: Generic!
    }
    """,
    query_type,
)
```


- - - - -


## `SchemaBindable`

```python
class SchemaBindable(Protocol):
    ...
```

Base class for [bindable](../Docs/bindables) types.

Subclasses should extend the `bind_to_schema` method with custom logic for
populating an instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic and values.


### Methods

#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `Schema[Bindable`](../Docs/bindables) instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).


### Example

Example `InputType` [bindable](../Docs/bindables) that sets Python names for fields of GraphQL input:

```python
from ariadne import SchemaBindable
from graphql import GraphQLInputType

class InputType(SchemaBindable):
    _name: str
    _fields: dict[str, str]

    def __init__(self, name: str, fields: dict[str, str] | None):
        self._name = name
        self._fields = fields or {}

    def set_field_out_name(self, field: str, out_name: str):
        self._fields[field] = out_name

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.get_type(self._name)
        if not graphql_type:
            raise ValueError(
                "Type %s is not defined in the schema" % self.name
            )
        if not isinstance(graphql_type, GraphQLInputType):
            raise ValueError(
                "%s is defined in the schema, but it is instance of %s (expected %s)"
                % (self.name, type(graphql_type).__name__, GraphQLInputType.__name__)
            )

        for field, out_name in self._fields.items():
            schema_field = graphql_type.fields.get(field)
            if not schema_field:
                raise ValueError(
                    "Type %s does not define the %s field" % (self.name, field)
                )

            schema_field.out_name = out_name
```

Usage:

```python
from ariadne import QueryType, make_executable_schema

from .input_type import InputType
from .users.models import User

input_type = InputType(
    "UserInput",
    {
        "fullName": "full_name",
        "yearOfBirth": "year_of_birth",
    }
)

query_type = QueryType()

@query_type.field("countUsers")
def resolve_count_users(*_, input):
    qs = User.objects

    if input:
        if input["full_name"]:
            qs = qs.filter(full_name__ilike=input["full_name"])
        if input["year_of_birth"]:
            qs = qs.filter(dob__year=input["year_of_birth"])

    return qs.count()


schema = make_executable_schema(
    """
    type Query {
        countUsers(input: UserInput!): Int!
    }

    input UserInput {
        fullName: String
        yearOfBirth: Int
    }
    """,
    query_type,
    input_type,
)
```


- - - - -


## `SchemaDirectiveVisitor`

```python
class SchemaDirectiveVisitor(SchemaVisitor):
    ...
```

Base class for custom GraphQL directives.

Also implements class methods with container and management logic for
directives at schema creation time, used by `make_executable_schema`.


### Lifecycle

Separate instances of the GraphQL directive are created for each GraphQL
schema item with the directive set on it. If directive is set on two
fields, two separate instances of a directive will be created.


### Constructor

```python
def __init__(self, name, args, visited_type, schema, context):
    ...
```

Instantiates the directive for schema object.


#### Required arguments

`name`: a `str` with directive's name.

`args`: a `dict` with directive's arguments.

`visited_type`: an GraphQL type this directive is set on.

`schema`: the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance.

`context`: `None`, unused but present for historic reasons.


### Methods

#### `get_directive_declaration`

```python
def get_directive_declaration(
    cls,
    directive_name: str,
    schema: GraphQLSchema,
) -> Optional[GraphQLDirective]:
    ...
```

Get GraphQL directive declaration from [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) by it's name.

Returns `GraphQLDirective` object or `None`.


##### Required arguments

`directive_name`: a `str` with name of directive in the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

`schema`: a [`GraphQLSchema`](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance to retrieve the directive
declaration from.


#### `get_declared_directives`

```python
def get_declared_directives(
    cls,
    schema: GraphQLSchema,
    directive_visitors: Dict[str, Type['SchemaDirectiveVisitor']],
) -> Dict[str, GraphQLDirective]:
    ...
```

Get GraphQL directives declaration from [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) by their names.

Returns a `dict` where keys are strings with directive names in schema
and values are `GraphQLDirective` objects with their declarations in the
[GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).


##### Required arguments

`directive_name`: a `str` with name of directive in the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

`schema`: a [`GraphQLSchema`](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance to retrieve the directive
declaration from.


#### `visit_schema_directives`

```python
def visit_schema_directives(
    cls,
    schema: GraphQLSchema,
    directive_visitors: Dict[str, Type['SchemaDirectiveVisitor']],
    *,
    context: Optional[Dict[str, Any]],
) -> Mapping[str, List['SchemaDirectiveVisitor']]:
    ...
```

Apply directives to the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

Applied directives mutate the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) in place.

Returns dict with names of GraphQL directives as keys and list of
directive instances created for each directive name.


##### Required arguments

`schema`: a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to which directives should be applied.

`directive_visitors`: a `dict` with `str` and
`Type[SchemaDirectiveVisitor]` pairs defining mapping of
`SchemaDirectiveVisitor` types to their names in the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).


##### Optional arguments

`context`: `None`, unused but present for historic reasons.


### Example schema visitors

`SchemaDirectiveVisitor` subclasses can implement any of below methods
that will be called when directive is applied to different elements of
[GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema):

```python
from ariadne import SchemaDirectiveVisitor
from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
)

class MyDirective(SchemaDirectiveVisitor):
    def visit_schema(self, schema: GraphQLSchema) -> None:
        pass

    def visit_scalar(self, scalar: GraphQLScalarType) -> GraphQLScalarType:
        pass

    def visit_object(self, object_: GraphQLObjectType) -> GraphQLObjectType:
        pass

    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        pass

    def visit_argument_definition(
        self,
        argument: GraphQLArgument,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLArgument:
        pass

    def visit_interface(self, interface: GraphQLInterfaceType) -> GraphQLInterfaceType:
        pass

    def visit_union(self, union: GraphQLUnionType) -> GraphQLUnionType:
        pass

    def visit_enum(self, type_: GraphQLEnumType) -> GraphQLEnumType:
        pass

    def visit_enum_value(
        self, value: GraphQLEnumValue, enum_type: GraphQLEnumType
    ) -> GraphQLEnumValue:
        pass

    def visit_input_object(
        self, object_: GraphQLInputObjectType
    ) -> GraphQLInputObjectType:
        pass

    def visit_input_field_definition(
        self, field: GraphQLInputField, object_type: GraphQLInputObjectType
    ) -> GraphQLInputField:
        pass
```


- - - - -


## `SchemaNameConverter`

```python
SchemaNameConverter = Callable[[str, GraphQLSchema, Tuple[str, ...]], str]
```

A type of a function implementing a strategy for names conversion in schema. Passed as an option to `make_executable_schema` and `convert_schema_names` functions.

Takes three arguments:

`name`: a `str` with schema name to convert.

`schema`: the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) in which names are converted.

`path`: a tuple of `str` representing a path to the schema item which name is being converted.

Returns a string with the Python name to use.


- - - - -


## `SnakeCaseFallbackResolversSetter`

```python
class SnakeCaseFallbackResolversSetter(FallbackResolversSetter):
    ...
```

Subclass of `FallbackResolversSetter` that uses case-converting resolver
instead of `default_field_resolver`.

> **Deprecated:** Use `convert_names_case` from `make_executable_schema`
instead.


### Methods

#### `add_resolver_to_field`

```python
def add_resolver_to_field(
    self,
    field_name: str,
    field_object: GraphQLField,
) -> None:
    ...
```

Sets case converting resolver on a field that doesn't have any.


- - - - -


## `SubscriptionType`

```python
class SubscriptionType(ObjectType):
    ...
```

[Bindable](../Docs/bindables) populating the Subscription type in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic.

Extends `ObjectType`, providing `source` decorator and `set_source` method, used
to set subscription sources for it's fields.


### Subscription sources ("subscribers")

Subscription source is a function that is an async generator. This function is used
to subscribe to source of events or messages. It can also filter the messages
by not yielding them.

Its signature is same as resolver:

```python
async def source_fn(
    root_value: Any, info: GraphQLResolveInfo, **field_args
) -> Any:
    yield ...
```


### Subscription resolvers

Subscription resolvers are called with message returned from the source. Their role
is to convert this message into Python representation of a type associated with
subscription's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema). Its called with message yielded from
source function as first argument.

```python
def resolver_fn(
    message: Any, info: GraphQLResolveInfo, **field_args
) -> Any:
    # Subscription resolver can be sync and async.
    return ...
```


### GraphQL arguments

When subscription field has arguments those arguments values are passed
to both source and resolver functions.


### Constructor

```python
def __init__(self):
    ...
```

Initializes the `SubscriptionType` with a GraphQL name set to `Subscription`.


### Methods

#### `source`

```python
def source(self, name: str) -> Callable[[Subscriber], Subscriber]:
    ...
```

Return a decorator that sets decorated function as a source for named field.

Wrapper for `create_register_subscriber` that on runtime validates `name` to be a
string.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind decorated source to.


#### `create_register_subscriber`

```python
def create_register_subscriber(
    self,
    name: str,
) -> Callable[[Subscriber], Subscriber]:
    ...
```

Return a decorator that sets decorated function as a source for named field.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind decorated source to.


#### `set_source`

```python
def set_source(self, name, generator: Subscriber) -> Subscriber:
    ...
```

Set a source for the field name.


##### Required arguments

`name`: a `str` with a name of the GraphQL object's field in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
set this source for.

`generator`: a `Subscriber` function to use as an source.


#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `SubscriptionType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

If it has any previously set subscription resolvers or source functions,
those will be replaced with new ones from this instance.


#### `bind_subscribers_to_graphql_type`

```python
def bind_subscribers_to_graphql_type(self, graphql_type) -> None:
    ...
```

Binds this `SubscriptionType` instance's source functions.

Source functions are set to fields `subscribe` attributes.


### Example source and resolver

```python
from ariadne import SubscriptionType, make_executable_schema
from broadcast import broadcast

from .models import Post


subscription_type = SubscriptionType()


@subscription_type.source("post")
async def source_post(*_, category: Optional[str] = None) -> dict:
    async with broadcast.subscribe(channel="NEW_POSTS") as subscriber:
        async for event in subscriber:
            message = json.loads(event.message)
            # Send message to resolver if we don't filter
            if not category or message["category"] == category:
                yield message


@subscription_type.field("post")
async def resolve_post(
    message: dict, *_, category: Optional[str] = None
) -> Post:
    # Convert message to Post object that resolvers for Post type in
    # GraphQL schema understand.
    return await Post.get_one(id=message["post_id"])


schema = make_executable_schema(
    """
    type Query {
        "Valid schema must define the Query type"
        none: Int
    }

    type Subscription {
        post(category: ID): Post!
    }

    type Post {
        id: ID!
        author: String!
        text: String!
    }
    """,
    subscription_type
)
```


### Example chat

[Ariadne GraphQL Chat Example](https://github.com/mirumee/ariadne-graphql-chat-example)
is the Github repository with GraphQL chat application, using Redis message backend,
Broadcaster library for publishing and subscribing to messages and React.js client
using Apollo-Client subscriptions.


- - - - -


## `UnionType`

```python
class UnionType(SchemaBindable):
    ...
```

[Bindable](../Docs/bindables) populating interfaces in a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with Python logic.


### Type resolver

Because GraphQL fields using union as their returning type can return any
Python value from their resolver, GraphQL unions require special type of
resolver called "type resolver" to function.

This resolver is called with the value returned by field's resolver and is
required to return a string with a name of GraphQL type represented by Python
value from the field:

```python
def example_type_resolver(obj: Any, *_) -> str:
    if isinstance(obj, PythonReprOfUser):
        return "USer"

    if isinstance(obj, PythonReprOfComment):
        return "Comment"

    raise ValueError(f"Don't know GraphQL type for '{obj}'!")
```

This resolver is not required if the GraphQL field returns a value that has
the `__typename` attribute or `dict` key with a name of the GraphQL type:

```python
user_data_dict = {"__typename": "User", ...}

# or...

class UserRepr:
    __typename: str = "User"
```


### Constructor

```python
def __init__(
    self,
    name: str,
    type_resolver: Optional[Resolver] = None,
):
    ...
```

Initializes the `UnionType` with a `name` and optional `type_resolver`.

Type resolver is required by `UnionType` to function properly, but can
be set later using either `set_type_resolver(type_resolver)`
setter or `type_resolver` decorator.


#### Required arguments

`name`: a `str` with the name of GraphQL union type in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to
bind to.


#### Optional arguments

`type_resolver`: a `Resolver` used to resolve a str with name of GraphQL type
from it's Python representation.


### Methods

#### `set_type_resolver`

```python
def set_type_resolver(self, type_resolver: Resolver) -> Resolver:
    ...
```

Sets function as type resolver for this union.

Can be used as a decorator. Also available through `type_resolver` alias:

```python
union_type = UnionType("MyUnion")

@union_type.type_resolver
def type_resolver(obj: Any, *_) -> str:
    ...
```


#### `bind_to_schema`

```python
def bind_to_schema(self, schema: GraphQLSchema) -> None:
    ...
```

Binds this `UnionType` instance to the instance of [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

Sets `resolve_type` attribute on GraphQL union. If this attribute was
previously set, it will be replaced to new value.


#### `validate_graphql_type`

```python
def validate_graphql_type(
    self,
    graphql_type: Optional[GraphQLNamedType],
) -> None:
    ...
```

Validates that schema's GraphQL type associated with this `UnionType`
is an `union`.


### Example

Following code creates a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) with a field that returns random
result of either `User` or `Post` GraphQL type. It also supports dict with
`__typename` key that explicitly declares its GraphQL type:

```python
import random
from dataclasses import dataclass
from ariadne import QueryType, UnionType, make_executable_schema

@dataclass
class UserModel:
    id: str
    name: str

@dataclass
class PostModel:
    id: str
    message: str

results = (
    UserModel(id=1, name="Bob"),
    UserModel(id=2, name="Alice"),
    UserModel(id=3, name="Jon"),
    PostModel(id=1, message="Hello world!"),
    PostModel(id=2, message="How's going?"),
    PostModel(id=3, message="Sure thing!"),
    {"__typename": "User", "id": 4, "name": "Polito"},
    {"__typename": "User", "id": 5, "name": "Aerith"},
    {"__typename": "Post", "id": 4, "message": "Good day!"},
    {"__typename": "Post", "id": 5, "message": "Whats up?"},
)

query_type = QueryType()

@query_type.field("result")
def resolve_random_result(*_):
    return random.choice(results)


result_type = UnionType("Result")

@result_type.type_resolver
def resolve_result_type(obj: UserModel | PostModel | dict, *_) -> str:
    if isinstance(obj, UserModel):
        return "User"

    if isinstance(obj, PostModel):
        return "Post"

    if isinstance(obj, dict) and obj.get("__typename"):
        return obj["__typename"]

    raise ValueError(f"Don't know GraphQL type for '{obj}'!")


schema = make_executable_schema(
    """
    type Query {
        result: Result!
    }

    union Result = User | Post

    type User {
        id: ID!
        name: String!
    }

    type Post {
        id: ID!
        message: String!
    }
    """,
    query_type,
    result_type,
)
```


- - - - -


## `combine_multipart_data`

```python
def combine_multipart_data(
    operations: Union[dict, list],
    files_map: dict,
    files: FilesDict,
) -> Union[dict, list]:
    ...
```

Populates `operations` variables with `files` using the `files_map`.

Utility function for integration developers.

Mutates `operations` in place, but also returns it.


### Requires arguments

`operations`: a `list` or `dict` with GraphQL operations to populate the file
variables in. It contains `operationName`, `query` and `variables` keys, but
implementation only cares about `variables` being present.

`files_map`: a `dict` with mapping of `files` to `operations`. Keys correspond
to keys in `files dict`, values are lists of strings with paths (eg.:
`variables.key.0` maps to `operations["variables"]["key"]["0"]`).

`files`: a `dict` of files. Keys are strings, values are environment specific
representations of uploaded files.


### Example

Following example uses `combine_multipart_data` to populate the `image`
variable with file object from `files`, using the `files_map` to know
which variable to replace.

```python
# Single GraphQL operation
operations = {
    "operationName": "AvatarUpload",
    "query": """
        mutation AvatarUpload($type: String!, $image: Upload!) {
            avatarUpload(type: $type, image: $image) {
                success
                errors
            }
        }
    """,
    "variables": {"type": "SQUARE", "image": None}
}
files_map = {"0": ["variables.image"]}
files = {"0": UploadedFile(....)}

combine_multipart_data(operations, files_map, files

assert operations == {
    "variables": {"type": "SQUARE", "image": UploadedFile(....)}
}
```


- - - - -


## `convert_camel_case_to_snake`

```python
def convert_camel_case_to_snake(graphql_name: str) -> str:
    ...
```

Converts a string with `camelCase` name to `snake_case`.

Utility function used by Ariadne's name conversion logic for mapping GraphQL
names using the `camelCase` convention to Python counterparts in `snake_case`.

Returns a string with converted name.


### Required arguments

`graphql_name`: a `str` with name to convert.


### Example

All characters in converted name are lowercased:

```python
assert convert_camel_case_to_snake("URL") == "url"
```

`_` is inserted before every uppercase character that's not first and is not
preceded by other uppercase character:

```python
assert convert_camel_case_to_snake("testURL") == "test_url"
```

`_` is inserted before every uppercase character succeeded by lowercased
character:

```python
assert convert_camel_case_to_snake("URLTest") == "url_test"
```

`_` is inserted before every digit that's not first and is not preceded by
other digit:

```python
assert convert_camel_case_to_snake("Rfc123") == "rfc_123"
```


- - - - -


## `convert_kwargs_to_snake_case`

```python
def convert_kwargs_to_snake_case(func: Callable) -> Callable:
    ...
```

Decorator for resolvers recursively converting their kwargs to `snake_case`.

Converts keys in `kwargs` dict from `camelCase` to `snake_case` using the
`convert_camel_case_to_snake` function. Walks values recursively, applying
same conversion to keys of nested dicts and dicts in lists of elements.

Returns decorated resolver function.

> **Deprecated:** This decorator is deprecated and will be deleted in future
version of Ariadne. Set `out_name`s explicitly in your [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) or use
the `convert_schema_names` option on `make_executable_schema`.


- - - - -


## `convert_schema_names`

```python
def convert_schema_names(
    schema: GraphQLSchema,
    name_converter: Optional[SchemaNameConverter],
) -> None:
    ...
```

Set mappings in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) from `camelCase` names to `snake_case`.

This function scans [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) and:

If objects field has name in `camelCase` and this field doesn't have a
resolver already set on it, new resolver is assigned to it that resolves
it's value from object attribute or dict key named like `snake_case`
version of field's name.

If object's field has argument in `camelCase` and this argument doesn't have
the `out_name` attribute already set, this attribute is populated with
argument's name converted to `snake_case`

If input's field has name in `camelCase` and it's `out_name` attribute is
not already set, this attribute is populated with field's name converted
to `snake_case`.

Schema is mutated in place.

Generally you shouldn't call this function yourself, as its part of
`make_executable_schema` logic, but its part of public API for other
libraries to use.


### Required arguments

`schema`: a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) to update.

`name_converter`: an `SchemaNameConverter` function to use to convert the
names from `camelCase` to `snake_case`. If not provided, default one
based on `convert_camel_case_to_snake` is used.


- - - - -


## `fallback_resolvers`

```python
fallback_resolvers = FallbackResolversSetter()
```

[Bindable](../Docs/bindables) instance of `FallbackResolversSetter`.

> **Deprecated:** This utility will be removed in future Ariadne release.
> 
> See `FallbackResolversSetter` for details.


- - - - -


## `format_error`

```python
def format_error(error: GraphQLError, debug: bool = False) -> dict:
    ...
```

Format the GraphQL error into JSON serializable format.

If `debug` is set to `True`, error's JSON will also include the [`extensions`](types-reference#extensions)
key with `exception` object containing error's `context` and `stacktrace`.

Returns a JSON-serializable `dict` with error representation.


### Required arguments

`error`: an `GraphQLError` to convert into JSON serializable format.


### Optional arguments

`debug`: a `bool` that controls if debug data should be included in
result `dict`. Defaults to `False`.


- - - - -


## `get_error_extension`

```python
def get_error_extension(error: GraphQLError) -> Optional[dict]:
    ...
```

Get a JSON-serializable `dict` containing error's stacktrace and context.

Returns a JSON-serializable `dict` with `stacktrace` and `context` to include
under error's [`extensions`](types-reference#extensions) key in JSON response. Returns `None` if `error`
has no stacktrace or wraps no exception.


### Required arguments

`error`: an `GraphQLError` to return context and stacktrace for.


- - - - -


## `get_formatted_error_context`

```python
def get_formatted_error_context(error: Exception) -> Optional[dict]:
    ...
```

Get JSON-serializable context from `Exception`.

Returns a `dict` of strings, with every key being value name and value
being `repr()` of it's Python value. Returns `None` if context is not
available.


### Required arguments

`error`: an `Exception` to return formatted context for.


- - - - -


## `get_formatted_error_traceback`

```python
def get_formatted_error_traceback(error: Exception) -> List[str]:
    ...
```

Get JSON-serializable stacktrace from `Exception`.

Returns list of strings, with every item being separate line from stacktrace.

This approach produces better results in GraphQL explorers which display every
line under previous one but not always format linebreak characters for blocks
of text.


### Required arguments

`error`: an `Exception` to return formatted stacktrace for.


- - - - -


## `gql`

```python
def gql(value: str) -> str:
    ...
```

Verifies that given string is a valid GraphQL.

Provides definition time validation for GraphQL strings. Returns unmodified
string. Some IDEs provide GraphQL syntax for highlighting those strings.


### Examples

Python string in this code snippet will use GraphQL's syntax highlighting when
viewed in VSCode:

```python
type_defs = gql(
    """
    type Query {
        hello: String!
    }
    """
)
```

This code will raise a GraphQL parsing error:

```python
type_defs = gql(
    """
    type Query {
        hello String!
    }
    """
)
```


- - - - -


## `graphql`

```python
async def graphql(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any],
    root_value: Optional[RootValue],
    query_parser: Optional[QueryParser],
    query_validator: Optional[QueryValidator],
    query_document: Optional[DocumentNode],
    debug: bool,
    introspection: bool,
    logger: Union[None, str, Logger, LoggerAdapter],
    validation_rules: Optional[ValidationRules],
    require_query: bool,
    error_formatter: ErrorFormatter,
    middleware: MiddlewareList,
    middleware_manager_class: Optional[Type[MiddlewareManager]],
    extensions: Optional[ExtensionList],
    execution_context_class: Optional[Type[ExecutionContext]],
    **kwargs,
) -> GraphQLResult:
    ...
```

Execute GraphQL query asynchronously.

Returns a tuple with two items:

`bool`: `True` when no errors occurred, `False` otherwise.

`dict`: an JSON-serializable `dict` with query result
(defining either `data`, `error`, or both keys) that should be returned to
client.


### Required arguments

`schema`: a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance that defines `Query` type.

`data`: a `dict` with query data (`query` string, optionally `operationName`
string and `variables` dictionary).


### Optional arguments

`context_value`: a context value to make accessible as 'context' attribute
of second argument (`info`) passed to resolvers.

`root_value`: a [`RootValue`](types-reference#rootvalue) to pass as first argument to resolvers set on
`Query` and `Mutation` types.

`query_parser`: a [`QueryParser`](types-reference#queryparser) to use instead of default one. Is called
with two arguments: `context_value`, and `data` dict.

`query_validator`: a `QueryValidator` to use instead of default one. Is called
with five arguments: `schema`, 'document_ast', 'rules', 'max_errors' and 'type_info'.

`query_document`: an already parsed GraphQL query. Setting this option will
prevent `graphql` from parsing `query` string from `data` second time.

`debug`: a `bool` for enabling debug mode. Controls presence of debug data
in errors reported to client.

`introspection`: a `bool` for disabling introspection queries.

`logger`: a `str` with name of logger or logger instance to use for logging
errors.

`validation_rules`: a `list` of or callable returning list of custom
validation rules to use to validate query before it's executed.

`require_query`: a `bool` controlling if GraphQL operation to execute must be
a query (vs. mutation or subscription).

`error_formatter`: an [`ErrorFormatter`](types-reference#errorformatter) callable to use to convert GraphQL
errors encountered during query execution to JSON-serializable format.

`middleware`: a `list` of or callable returning list of GraphQL middleware
to use by query executor.

`middleware_manager_class`: a `MiddlewareManager` class to use by query
executor.

[`extensions`](types-reference#extensions): a `list` of or callable returning list of extensions
to use during query execution.

`execution_context_class`: `ExecutionContext` class to use by query
executor.

`**kwargs`: any kwargs not used by `graphql` are passed to
`graphql.graphql`.


- - - - -


## `graphql_sync`

```python
def graphql_sync(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any],
    root_value: Optional[RootValue],
    query_parser: Optional[QueryParser],
    query_validator: Optional[QueryValidator],
    query_document: Optional[DocumentNode],
    debug: bool,
    introspection: bool,
    logger: Union[None, str, Logger, LoggerAdapter],
    validation_rules: Optional[ValidationRules],
    require_query: bool,
    error_formatter: ErrorFormatter,
    middleware: MiddlewareList,
    middleware_manager_class: Optional[Type[MiddlewareManager]],
    extensions: Optional[ExtensionList],
    execution_context_class: Optional[Type[ExecutionContext]],
    **kwargs,
) -> GraphQLResult:
    ...
```

Execute GraphQL query synchronously.

Returns a tuple with two items:

`bool`: `True` when no errors occurred, `False` otherwise.

`dict`: an JSON-serializable `dict` with query result
(defining either `data`, `error`, or both keys) that should be returned to
client.


### Required arguments

`schema`: a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance that defines `Query` type.

`data`: a `dict` with query data (`query` string, optionally `operationName`
string and `variables` dictionary).


### Optional arguments

`context_value`: a context value to make accessible as 'context' attribute
of second argument (`info`) passed to resolvers.

`root_value`: a [`RootValue`](types-reference#rootvalue) to pass as first argument to resolvers set on
`Query` and `Mutation` types.

`query_parser`: a [`QueryParser`](types-reference#queryparser) to use instead of default one. Is called
with two arguments: `context_value`, and `data` dict.

`query_validator`: a `QueryValidator` to use instead of default one. Is called
with five arguments: `schema`, 'document_ast', 'rules', 'max_errors' and 'type_info'.

`query_document`: an already parsed GraphQL query. Setting this option will
prevent `graphql_sync` from parsing `query` string from `data` second time.

`debug`: a `bool` for enabling debug mode. Controls presence of debug data
in errors reported to client.

`introspection`: a `bool` for disabling introspection queries.

`logger`: a `str` with name of logger or logger instance to use for logging
errors.

`validation_rules`: a `list` of or callable returning list of custom
validation rules to use to validate query before it's executed.

`require_query`: a `bool` controlling if GraphQL operation to execute must be
a query (vs. mutation or subscription).

`error_formatter`: an [`ErrorFormatter`](types-reference#errorformatter) callable to use to convert GraphQL
errors encountered during query execution to JSON-serializable format.

`middleware`: a `list` of or callable returning list of GraphQL middleware
to use by query executor.

`middleware_manager_class`: a `MiddlewareManager` class to use by query
executor.

[`extensions`](types-reference#extensions): a `list` of or callable returning list of extensions
to use during query execution.

`execution_context_class`: `ExecutionContext` class to use by query
executor.

`**kwargs`: any kwargs not used by `graphql_sync` are passed to
`graphql.graphql_sync`.


- - - - -


## `is_default_resolver`

```python
def is_default_resolver(resolver: Optional[Resolver]) -> bool:
    ...
```

Test if resolver function is default resolver implemented by
`graphql-core` or Ariadne.

Returns `True` if resolver function is `None`, `graphql.default_field_resolver`
or was created by Ariadne's `resolve_to` utility. Returns `False` otherwise.

`True` is returned for `None` because query executor defaults to the
`graphql.default_field_resolver` is there's no resolver function set on a
field.


### Required arguments

`resolver`: an function `None` to test or `None`.


- - - - -


## `load_schema_from_path`

```python
def load_schema_from_path(path: Union[str, os.PathLike]) -> str:
    ...
```

Load schema definition in Schema Definition Language from file or directory.

If `path` argument points to a file, this file's contents are read, validated
and returned as `str`. If its a directory, its walked recursively and every
file with `.graphql`, `.graphqls` or `.gql` extension is read and validated,
and all files are then concatenated into single `str` that is then returned.

Returns a `str` with schema definition that was already validated to be valid
GraphQL SDL. Raises `GraphQLFileSyntaxError` is any of loaded files fails to
parse.


### Required arguments

`path`: a `str` or `PathLike` object pointing to either file or directory
with files to load.


- - - - -


## `make_executable_schema`

```python
def make_executable_schema(
    type_defs: Union[str, List[str]],
    *bindables: SchemaBindables,
    directives: Optional[Dict[str, Type[SchemaDirectiveVisitor]]],
    convert_names_case: Union[bool, SchemaNameConverter],
) -> GraphQLSchema:
    ...
```

Create a [`GraphQLSchema`](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance that can be used to execute queries.

Returns a [`GraphQLSchema`](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance with attributes populated with Python
values and functions.


### Required arguments

`type_defs`: a `str` or list of `str` with GraphQL types definitions in
schema definition language (`SDL`).


### Optional arguments

[`bindables`](../Docs/bindables): instances or lists of instances of schema [bindables](../Docs/bindables). Order in
which [bindables](../Docs/bindables) are passed to `make_executable_schema` matters depending on
individual [bindable](../Docs/bindables)'s implementation.

`directives`: a dict of GraphQL directives to apply to schema. Dict's keys must
correspond to directives names in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) and values should be
`SchemaDirectiveVisitor` classes (_not_ instances) implementing their logic.

`convert_names_case`: a `bool` or function of `SchemaNameConverter` type to
use to convert names in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) between `camelCase` used by GraphQL
and `snake_case` used by Python. Defaults to `False`, making all conversion
explicit and up to developer to implement. Set `True` to use
default strategy using `convert_camel_case_to_snake` for name conversions or
set to custom function to customize this behavior.


### Example with minimal schema

Below code creates minimal executable schema that doesn't implement any Python
logic, but still executes queries using `root_value`:

```python
from ariadne import graphql_sync, make_executable_schema

schema = make_executable_schema(
    """
    type Query {
        helloWorld: String!
    }
    """
)

no_errors, result = graphql_sync(
    schema,
    {"query": "{ helloWorld }"},
    root_value={"helloWorld": "Hello world!"},
)

assert no_errors
assert result == {
    "data": {
        "helloWorld": "Hello world!",
    },
}
```


### Example with bindables

Below code creates executable schema that combines different ways of passing
[bindables](../Docs/bindables) to add Python logic to schema:

```python
from dataclasses import dataclass
from enum import Enum
from ariadne import ObjectType, QueryType, UnionType, graphql_sync, make_executable_schema

# Define some types representing database models in real applications
class UserLevel(str, Enum):
    USER = "user"
    ADMIN = "admin"

@dataclass
class UserModel:
    id: str
    name: str
    level: UserLevel

@dataclass
class PostModel:
    id: str
    body: str

# Create fake "database"
results = (
    UserModel(id=1, name="Bob", level=UserLevel.USER),
    UserModel(id=2, name="Alice", level=UserLevel.ADMIN),
    UserModel(id=3, name="Jon", level=UserLevel.USER),
    PostModel(id=1, body="Hello world!"),
    PostModel(id=2, body="How's going?"),
    PostModel(id=3, body="Sure thing!"),
)


# Resolve username field in GraphQL schema to user.name attribute
user_type = ObjectType("User")
user_type.set_alias("username", "name")


# Resolve message field in GraphQL schema to post.body attribute
post_type = ObjectType("Post")
post_type.set_alias("message", "body")


# Resolve results field in GraphQL schema to results array
query_type = QueryType()

@query_type.field("results")
def resolve_results(*_):
    return results


# Resolve GraphQL type of individual result from it's Python class
result_type = UnionType("Result")

@result_type.type_resolver
def resolve_result_type(obj: UserModel | PostModel | dict, *_) -> str:
    if isinstance(obj, UserModel):
        return "User"

    if isinstance(obj, PostModel):
        return "Post"

    raise ValueError(f"Don't know GraphQL type for '{obj}'!")


# Create executable schema that returns list of results
schema = make_executable_schema(
    """
    type Query {
        results: [Result!]!
    }

    union Result = User | Post

    type User {
        id: ID!
        username: String!
        level: UserLevel!
    }

    type Post {
        id: ID!
        message: String!
    }

    enum UserLevel {
        USER
        ADMIN
    }
    """,
    # Bindables *args accept single instances:
    query_type,
    result_type,
    # Bindables *args accepts lists of instances:
    [user_type, post_type],
    # Both approaches can be mixed
    # Python Enums are also valid bindables:
    UserLevel,
)

# Query the schema for results
no_errors, result = graphql_sync(
    schema,
    {
        "query": (
            """
            {
                results {
                    ... on Post {
                        id
                        message
                    }
                    ... on User {
                        id
                        username
                        level
                    }
                }
            }
            """
        ),
    },
)

# Verify that it works
assert no_errors
assert result == {
    "data": {
        "results": [
            {
                "id": "1",
                "username": "Bob",
                "level": "USER",
            },
            {
                "id": "2",
                "username": "Alice",
                "level": "ADMIN",
            },
            {
                "id": "3",
                "username": "Jon",
                "level": "USER",
            },
            {
                "id": "1",
                "message": "Hello world!",
            },
            {
                "id": "2",
                "message": "How's going?",
            },
            {
                "id": "3",
                "message": "Sure thing!",
            },
        ],
    },
}
```


### Example with directive

Below code uses `directives` option to set custom directive on schema:

```python
from functools import wraps
from ariadne import SchemaDirectiveVisitor, graphql_sync, make_executable_schema
from graphql import default_field_resolver

class UppercaseDirective(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        org_resolver = field.resolve or default_field_resolver

        @wraps(org_resolver)
        def uppercase_resolved_value(*args, **kwargs):
            value = org_resolver(*args, **kwargs)
            if isinstance(value, str):
                return value.upper()
            return value

        # Extend field's behavior by wrapping it's resolver in custom one
        field.resolve = uppercase_resolved_value
        return field


schema = make_executable_schema(
    """
    directive @uppercase on FIELD_DEFINITION

    type Query {
        helloWorld: String! @uppercase
    }
    """,
    directives={"uppercase": UppercaseDirective},
)

no_errors, result = graphql_sync(
    schema,
    {"query": "{ helloWorld }"},
    root_value={"helloWorld": "Hello world!"},
)

assert no_errors
assert result == {
    "data": {
        "helloWorld": "HELLO WORLD!",
    },
}
```


### Example with converted names

Below code uses `convert_names_case=True` option to resolve `helloWorld`
field to `hello_world` key from `root_value`:

```python
from ariadne import graphql_sync, make_executable_schema

schema = make_executable_schema(
    """
    type Query {
        helloWorld: String!
    }
    """,
    convert_names_case=True,
)

no_errors, result = graphql_sync(
    schema,
    {"query": "{ helloWorld }"},
    root_value={"hello_world": "Hello world!"},
)

assert no_errors
assert result == {
    "data": {
        "helloWorld": "Hello world!",
    },
}
```


- - - - -


## `repair_schema_default_enum_values`

```python
def repair_schema_default_enum_values(schema: GraphQLSchema) -> None:
    ...
```

Repairs Python values of default enums embedded in the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

Default enum values in the [GraphQL schemas](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) are represented as strings with enum
member names in Python. Assigning custom Python values to members of the
`GraphQLEnumType` doesn't change those defaults.

This function walks the [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema), finds default enum values strings and,
if this string is a valid GraphQL member name, swaps it out for a valid Python
value.


- - - - -


## `resolve_to`

```python
def resolve_to(attr_name: str) -> Resolver:
    ...
```

Create a resolver that resolves to given attribute or dict key.

Returns a resolver function that can be used as resolver.

Usually not used directly  but through higher level features like aliases
or schema names conversion.


### Required arguments

`attr_name`: a `str` with name of attribute or `dict` key to return from
resolved object.


- - - - -


## `snake_case_fallback_resolvers`

```python
snake_case_fallback_resolvers = SnakeCaseFallbackResolversSetter()
```

[Bindable](../Docs/bindables) instance of `SnakeCaseFallbackResolversSetter`.

> **Deprecated:** Use `convert_names_case` from `make_executable_schema` instead.


- - - - -


## `subscribe`

```python
async def subscribe(
    schema: GraphQLSchema,
    data: Any,
    *,
    context_value: Optional[Any],
    root_value: Optional[RootValue],
    query_parser: Optional[QueryParser],
    query_validator: Optional[QueryValidator],
    query_document: Optional[DocumentNode],
    debug: bool,
    introspection: bool,
    logger: Union[None, str, Logger, LoggerAdapter],
    validation_rules: Optional[ValidationRules],
    error_formatter: ErrorFormatter,
    **kwargs,
) -> SubscriptionResult:
    ...
```

Subscribe to GraphQL updates.

Returns a tuple with two items:

`bool`: `True` when no errors occurred, `False` otherwise.

`AsyncGenerator`: an async generator that server implementation should
consume to retrieve messages to send to client.


### Required arguments

'schema': a [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) instance that defines `Subscription` type.

`data`: a `dict` with query data (`query` string, optionally `operationName`
string and `variables` dictionary).


### Optional arguments

`context_value`: a context value to make accessible as 'context' attribute
of second argument (`info`) passed to resolvers and source functions.

`root_value`: a [`RootValue`](types-reference#rootvalue) to pass as first argument to resolvers and
source functions set on `Subscription` type.

`query_parser`: a [`QueryParser`](types-reference#queryparser) to use instead of default one. Is called
with two arguments: `context_value`, and `data` dict.

`query_validator`: a `QueryValidator` to use instead of default one. Is called
with five arguments: `schema`, 'document_ast', 'rules', 'max_errors' and 'type_info'.

`query_document`: an already parsed GraphQL query. Setting this option will
prevent `subscribe` from parsing `query` string from `data` second time.

`debug`: a `bool` for enabling debug mode. Controls presence of debug data
in errors reported to client.

`introspection`: a `bool` for disabling introspection queries.

`logger`: a `str` with name of logger or logger instance to use for logging
errors.

`validation_rules`: a `list` of or callable returning list of custom
validation rules to use to validate query before it's executed.

`error_formatter`: an [`ErrorFormatter`](types-reference#errorformatter) callable to use to convert GraphQL
errors encountered during query execution to JSON-serializable format.

`**kwargs`: any kwargs not used by `subscribe` are passed to
`graphql.subscribe`.


- - - - -


## `type_implements_interface`

```python
def type_implements_interface(
    interface: str,
    graphql_type: GraphQLType,
) -> bool:
    ...
```

Test if type definition from [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) implements an interface.

Returns `True` if type implements interface and `False` if it doesn't.


### Required arguments

`interface`: a `str` with name of interface in [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema).

`graphql_type`: a `GraphQLType` interface to test. It may or may not have
the `interfaces` attribute.


- - - - -


## `unwrap_graphql_error`

```python
def unwrap_graphql_error(
    error: Union[GraphQLError, Optional[Exception]],
) -> Optional[Exception]:
    ...
```

Recursively unwrap exception when its instance of GraphQLError.

GraphQL query executor wraps exceptions in `GraphQLError` instances which
contain information about exception's origin in GraphQL query or it's result.

Original exception is available through `GraphQLError`'s `original_error`
attribute, but sometimes `GraphQLError` can be wrapped in other `GraphQLError`.

Returns unwrapped exception or `None` if no original exception was found.


### Example

Below code unwraps original `KeyError` from multiple `GraphQLError` instances:

```python
error = KeyError("I am a test!")

assert unwrap_graphql_error(
    GraphQLError(
        "Error 1",
        GraphQLError(
            "Error 2",
            GraphQLError(
                "Error 3",
                original_error=error
            )
        )
    )
) == error
```

Passing other exception to `unwrap_graphql_error` results in same exception
being returned:

```python
error = ValueError("I am a test!")
assert unwrap_graphql_error(error) == error
```


- - - - -


## `upload_scalar`

```python
upload_scalar = ScalarType('Upload')
```

Optional Python logic for `Upload` scalar.

`Upload` scalar doesn't require any custom Python logic to work, but this utility sets `serializer` and `literal_parser` to raise ValueErrors when `Upload` is used either as return type for field or passed as literal value in GraphQL query.


### Example

Below code defines a schema with `Upload` scalar using `upload_scalar` utility:

```python
from ariadne import MutationType, make_executable_schema, upload_scalar

mutation_type = MutationType()

@mutation_type.field("handleUpload")
def resolve_handle_upload(*_, upload):
    return repr(upload)


schema = make_executable_schema(
    """
    scalar Upload

    type Query {
        empty: String
    }

    type Mutation {
        handleUpload(upload: Upload!): String
    }
    """,
    upload_scalar,
    mutation_type,
)
```


- - - - -


## `validate_schema_default_enum_values`

```python
def validate_schema_default_enum_values(schema: GraphQLSchema) -> None:
    ...
```

Raises `ValueError` if [GraphQL schema](https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema) has input fields or arguments with
default values that are undefined enum values.


### Example schema with invalid field argument

This schema fails to validate because argument `role` on field `users`
specifies `REVIEWER` as default value and `REVIEWER` is not a member of
the `UserRole` enum:

```graphql
type Query {
    users(role: UserRole = REVIEWER): [User!]!
}

enum UserRole {
    MEMBER
    MODERATOR
    ADMIN
}

type User {
    id: ID!
}
```


### Example schema with invalid input field

This schema fails to validate because field `role` on input `UserFilters`
specifies `REVIEWER` as default value and `REVIEWER` is not a member of
the `UserRole` enum:

```graphql
type Query {
    users(filter: UserFilters): [User!]!
}

input UserFilters {
    name: String
    role: UserRole = REVIEWER
}

enum UserRole {
    MEMBER
    MODERATOR
    ADMIN
}

type User {
    id: ID!
}
```


### Example schema with invalid default input field argument

This schema fails to validate because field `field` on input `ChildInput`
specifies `INVALID` as default value and `INVALID` is not a member of
the `Role` enum:

```graphql
type Query {
    field(arg: Input = {field: {field: INVALID}}): String
}

input Input {
    field: ChildInput
}

input ChildInput {
    field: Role
}

enum Role {
    USER
    ADMIN
}
```