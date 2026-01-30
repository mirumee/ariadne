---
id: inputs
title: Inputs
---

GraphQL Input types are method for collecting logically associated arguments under single GraphQL type.

For example, your mutation creating new issue in an issue tracker API could accept multiple arguments:

```graphql
type Mutation {
    issueCreate(
        title: String!
        description: String!
        labels: [String!]!
        priority: Int!
        isClosed: Boolean!
    ): IssueMutationResult!
}

type IssueMutationResult {
    error: Boolean
}
```

But you may also gather all those arguments under a single input type:

```graphql
type Mutation {
    issueCreate(
        input: IssueInput!
    ): IssueMutationResult!
}

input IssueInput {
    title: String!,
    description: String!
    labels: [String!]!
    priority: Int!
    isClosed: Boolean!
}

type IssueMutationResult {
    success: Boolean!
    error: String!
}
```

Now, when a client wants to create a new issue, they need to provide an `input` object that matches the `IssueInput` definition. This input will then be validated and passed to the mutation's resolver as a `dict` available under the `input` keyword argument:

```python
def resolve_issue_create(_, info, input: dict):
    clean_input = {
        "title": input["title"],
        "description": input["description"],
        "labels": input["labels"],
        "priority": input["priority"],
        "is_closed": input.get("isClosed"),
    }

    try:
        create_new_new_issue(info.context, clean_input)

        return {"success": True}
    except ValidationError as err:
        return {
            "success": False,
            "error": str(err),
        }
```

> **Note:** Don't worry about `input` and `clean_input` dicts for now. Next chapters of this guide will show you how to customize GraphQL's default behavior using Ariadne's utilities.

Another advantage of `input` types is that they are reusable. If we later decide to implement another mutation for updating the issue, we can do it like this:

```graphql
type Mutation {
    issueCreate(
        input: IssueInput!
    ): IssueMutationResult!
    issueUpdate(
        id: ID!
        input: IssueInput!
    ): IssueMutationResult!
}

input IssueInput {
    title: String!,
    description: String!
    labels: [String!]!
    priority: Int!
    isClosed: Boolean!
}

type IssueMutationResult {
    success: Boolean!
    error: String!
}
```

Our `issueUpdate` mutation will now accept two arguments: `id` and `input`:

```python
def resolve_issue_update(_, info, id: str, input: dict):
    issue = get_issue_from_db(id)

    clean_input = {
        "title": input["title"],
        "description": input["description"],
        "labels": input["labels"],
        "priority": input["priority"],
        "is_closed": input.get("isClosed"),
    }

    try:
        update_issue(info.context, issue, clean_input)

        return {"success": True}
    except ValidationError as err:
        return {
            "success": False,
            "error": err,
        }
```

You may wonder why you would want to use `input` instead of reusing an already-defined type. This is because input types provide some guarantees that regular objects don't: they are serializable, and they don't implement interfaces or unions. However, input fields are not limited to scalars. You can create fields that are lists, or even reference other inputs:

```graphql
input PollInput {
    question: String!,
    options: [PollOptionInput!]!
}

input PollOptionInput {
    label: String!
    color: String!
}
```

Lastly, take a note that inputs are not specific to mutations. You can use inputs for every argument in schema. For example, you can have an input with filtering options for fields returning lists of items.

## Custom mappings for input dicts

In above example input value was represented in Python as `dict`, with extra step for converting original dictionary to `clean_dict` that follows Pythonic convention for naming keys, expected by rest of application's business logic.

Those initial keys set on input `dict` by GraphQL are called "out names" and default to names of input's fields in GraphQL schema. Ariadne provides `InputType` utility that enables customization of those names. 

We can replace the logic used to create `clean_input` with `InputType`'s `out_names` option:

```python
from ariadne import InputType, MutationType, gql, make_executable_schema

type_defs = gql(
    """
    type Query {
        unused: Boolean
    }

    type Mutation {
        issueCreate(
            input: IssueInput!
        ): IssueMutationResult!
    }

    input IssueInput {
        title: String!,
        description: String!
        labels: [String!]!
        priority: Int!
        isClosed: Boolean!
    }

    type IssueMutationResult {
        success: Boolean!
        error: String!
    }
    """
)

mutation_type = MutationType()

@mutation_type.field("issueCreate")
def resolve_issue_create(_, info, input: dict):
    try:
        create_new_new_issue(info.context, input)

        return {"success": True}
    except ValidationError as err:
        return {
            "success": False,
            "error": str(err),
        }


schema = make_executable_schema(
    type_defs,
    mutation_type,
    InputType("IssueInput", out_names={"isClosed": "is_closed"}),
)
```

`InputType` utility accepts few arguments, but in this section we will focus on two:

- First argument, `name`, is a string of input type in GraphQL schema which's behavior we want to customize.
- `out_names` option is a `dict` with Python out names (`dict` values) for input fields (`dict` keys).

In the above example we are using the `out_names` option of `InputType` to tell GraphQL that in Python `dict` with input data, `isClosed` field's value should be put under the `is_closed` key.

We are passing this value as named argument because `out_names` is actually a third argument of `InputType`.

> **Note:** Instead of setting the `out_names` option for each input type, you can enable the `convert_names_case` option on `make_executable_schema` to set those automatically for entire schema.
>
> See [this guide](case-conversion) for the details.


## Representing GraphQL inputs with custom Python types

`InputType`'s second and more powerful option is setting GraphQL input's "out type". "Out type" is custom deserialization logic that's ran by GraphQL against input's final `dict` (`dict` created using `out_names`). This custom logic can be used to do anything with input's `dict` data, included converting it other Python type.

For example, we could represent `IssueInput` in Python as data class:

```python
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class IssueInput:
    title: str
    description: str
    labels: List[str]
    priority: int
    is_closed: Optional[bool] = None
```

Then we could define custom logic converting dict with input's data to this class:

```python
def get_issue_input_repr(data: dict) -> IssueInput:
    return IssueInput(**data)
```

Finally, we need update `InputType` to use this function for creating Python representation of `IssueInput` GraphQL type:

```python
schema = make_executable_schema(
    type_defs,
    mutation_type,
    InputType(
        "IssueInput",
        get_issue_input_repr,
        {"isClosed": "is_closed"},
    ),
)
```

But in final code we can use lambda function instead of `get_issue_input_repr`:

```python
from dataclasses import dataclass
from typing import List, Optional

from ariadne import InputType, MutationType, gql, make_executable_schema

type_defs = gql(
    """
    type Query {
        unused: Boolean
    }

    type Mutation {
        issueCreate(
            input: IssueInput!
        ): IssueMutationResult!
    }

    input IssueInput {
        title: String!,
        description: String!
        labels: [String!]!
        priority: Int!
        isClosed: Boolean!
    }

    type IssueMutationResult {
        success: Boolean!
        error: String!
    }
    """
)


@dataclass
class IssueInput:
    title: str
    description: str
    labels: List[str]
    priority: int
    is_closed: Optional[bool] = None


mutation_type = MutationType()

@mutation_type.field("issueCreate")
def resolve_issue_create(_, info, input: IssueInput):
    try:
        create_new_new_issue(info.context, input)

        return {"success": True}
    except ValidationError as err:
        return {
            "success": False,
            "error": str(err),
        }


schema = make_executable_schema(
    type_defs,
    mutation_type,
    InputType(
        "IssueInput",
        lambda data: IssueInput(**data),
        {"isClosed": "is_closed"},
    ),
)
```

Thats it! `IssueInput` in GraphQL schema will now be represented as `IssueInput` dataclass in Python logic.