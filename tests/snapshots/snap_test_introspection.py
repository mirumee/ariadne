# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_executable_schema_can_be_introspected 1"] = {
    "__schema": {
        "directives": [
            {
                "args": [
                    {
                        "defaultValue": None,
                        "description": "Included when true.",
                        "name": "if",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    }
                ],
                "description": "Directs the executor to include this field or fragment only when the `if` argument is true.",
                "locations": ["FIELD", "FRAGMENT_SPREAD", "INLINE_FRAGMENT"],
                "name": "include",
            },
            {
                "args": [
                    {
                        "defaultValue": None,
                        "description": "Skipped when true.",
                        "name": "if",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    }
                ],
                "description": "Directs the executor to skip this field or fragment when the `if` argument is true.",
                "locations": ["FIELD", "FRAGMENT_SPREAD", "INLINE_FRAGMENT"],
                "name": "skip",
            },
            {
                "args": [
                    {
                        "defaultValue": '"No longer supported"',
                        "description": "Explains why this element was deprecated, usually also including a suggestion for how toaccess supported similar data. Formatted in [Markdown](https://daringfireball.net/projects/markdown/).",
                        "name": "reason",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    }
                ],
                "description": "Marks an element of a GraphQL schema as no longer supported.",
                "locations": ["FIELD_DEFINITION", "ENUM_VALUE"],
                "name": "deprecated",
            },
        ],
        "mutationType": None,
        "queryType": {"name": "Query"},
        "subscriptionType": None,
        "types": [
            {
                "description": None,
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "test",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [
                            {
                                "defaultValue": None,
                                "description": None,
                                "name": "id",
                                "type": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "SCALAR",
                                        "name": "Int",
                                        "ofType": None,
                                    },
                                },
                            }
                        ],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "user",
                        "type": {"kind": "OBJECT", "name": "User", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "users",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "User",
                                        "ofType": None,
                                    },
                                },
                            },
                        },
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "Query",
                "possibleTypes": None,
            },
            {
                "description": "The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.",
                "enumValues": None,
                "fields": None,
                "inputFields": None,
                "interfaces": None,
                "kind": "SCALAR",
                "name": "String",
                "possibleTypes": None,
            },
            {
                "description": "The `Int` scalar type represents non-fractional signed whole numeric values. Int can represent values between -(2^31 - 1) and 2^31 - 1 since represented in JSON as double-precision floating point numbers specifiedby [IEEE 754](http://en.wikipedia.org/wiki/IEEE_floating_point).",
                "enumValues": None,
                "fields": None,
                "inputFields": None,
                "interfaces": None,
                "kind": "SCALAR",
                "name": "Int",
                "possibleTypes": None,
            },
            {
                "description": None,
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "name",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "age",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {"kind": "SCALAR", "name": "Int", "ofType": None},
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "dateOfBirth",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Date",
                                "ofType": None,
                            },
                        },
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "User",
                "possibleTypes": None,
            },
            {
                "description": None,
                "enumValues": None,
                "fields": None,
                "inputFields": None,
                "interfaces": None,
                "kind": "SCALAR",
                "name": "Date",
                "possibleTypes": None,
            },
            {
                "description": "A GraphQL Schema defines the capabilities of a GraphQL server. It exposes all available types and directives on the server, as well as the entry points for query, mutation and subscription operations.",
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": "A list of all types supported by this server.",
                        "isDeprecated": False,
                        "name": "types",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__Type",
                                        "ofType": None,
                                    },
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": "The type that query operations will be rooted at.",
                        "isDeprecated": False,
                        "name": "queryType",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "OBJECT",
                                "name": "__Type",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": "If this server supports mutation, the type that mutation operations will be rooted at.",
                        "isDeprecated": False,
                        "name": "mutationType",
                        "type": {"kind": "OBJECT", "name": "__Type", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": "If this server support subscription, the type that subscription operations will be rooted at.",
                        "isDeprecated": False,
                        "name": "subscriptionType",
                        "type": {"kind": "OBJECT", "name": "__Type", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": "A list of all directives supported by this server.",
                        "isDeprecated": False,
                        "name": "directives",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__Directive",
                                        "ofType": None,
                                    },
                                },
                            },
                        },
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "__Schema",
                "possibleTypes": None,
            },
            {
                "description": """The fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.""",
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "kind",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "ENUM",
                                "name": "__TypeKind",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "name",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "description",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [
                            {
                                "defaultValue": "false",
                                "description": None,
                                "name": "includeDeprecated",
                                "type": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            }
                        ],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "fields",
                        "type": {
                            "kind": "LIST",
                            "name": None,
                            "ofType": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__Field",
                                    "ofType": None,
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "interfaces",
                        "type": {
                            "kind": "LIST",
                            "name": None,
                            "ofType": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__Type",
                                    "ofType": None,
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "possibleTypes",
                        "type": {
                            "kind": "LIST",
                            "name": None,
                            "ofType": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__Type",
                                    "ofType": None,
                                },
                            },
                        },
                    },
                    {
                        "args": [
                            {
                                "defaultValue": "false",
                                "description": None,
                                "name": "includeDeprecated",
                                "type": {
                                    "kind": "SCALAR",
                                    "name": "Boolean",
                                    "ofType": None,
                                },
                            }
                        ],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "enumValues",
                        "type": {
                            "kind": "LIST",
                            "name": None,
                            "ofType": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__EnumValue",
                                    "ofType": None,
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "inputFields",
                        "type": {
                            "kind": "LIST",
                            "name": None,
                            "ofType": {
                                "kind": "NON_NULL",
                                "name": None,
                                "ofType": {
                                    "kind": "OBJECT",
                                    "name": "__InputValue",
                                    "ofType": None,
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "ofType",
                        "type": {"kind": "OBJECT", "name": "__Type", "ofType": None},
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "__Type",
                "possibleTypes": None,
            },
            {
                "description": "An enum describing what kind of type a given `__Type` is",
                "enumValues": [
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is a scalar.",
                        "isDeprecated": False,
                        "name": "SCALAR",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is an object. `fields` and `interfaces` are valid fields.",
                        "isDeprecated": False,
                        "name": "OBJECT",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is an interface. `fields` and `possibleTypes` are valid fields.",
                        "isDeprecated": False,
                        "name": "INTERFACE",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is a union. `possibleTypes` is a valid field.",
                        "isDeprecated": False,
                        "name": "UNION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is an enum. `enumValues` is a valid field.",
                        "isDeprecated": False,
                        "name": "ENUM",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is an input object. `inputFields` is a valid field.",
                        "isDeprecated": False,
                        "name": "INPUT_OBJECT",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is a list. `ofType` is a valid field.",
                        "isDeprecated": False,
                        "name": "LIST",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Indicates this type is a non-null. `ofType` is a valid field.",
                        "isDeprecated": False,
                        "name": "NON_NULL",
                    },
                ],
                "fields": None,
                "inputFields": None,
                "interfaces": None,
                "kind": "ENUM",
                "name": "__TypeKind",
                "possibleTypes": None,
            },
            {
                "description": "The `Boolean` scalar type represents `true` or `false`.",
                "enumValues": None,
                "fields": None,
                "inputFields": None,
                "interfaces": None,
                "kind": "SCALAR",
                "name": "Boolean",
                "possibleTypes": None,
            },
            {
                "description": "Object and Interface types are described by a list of Fields, each of which has a name, potentially a list of arguments, and a return type.",
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "name",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "description",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "args",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__InputValue",
                                        "ofType": None,
                                    },
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "type",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "OBJECT",
                                "name": "__Type",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "isDeprecated",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "deprecationReason",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "__Field",
                "possibleTypes": None,
            },
            {
                "description": "Arguments provided to Fields or Directives and the input fields of an InputObject are represented as Input Values which describe their type and optionally a default value.",
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "name",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "description",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "type",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "OBJECT",
                                "name": "__Type",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "defaultValue",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "__InputValue",
                "possibleTypes": None,
            },
            {
                "description": "One possible value for a given Enum. Enum values are unique values, not a placeholder for a string or numeric value. However an Enum value is returned in a JSON response as a string.",
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "name",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "description",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "isDeprecated",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "deprecationReason",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "__EnumValue",
                "possibleTypes": None,
            },
            {
                "description": """A Directive provides a way to describe alternate runtime execution and type validation behavior in a GraphQL document.

In some cases, you need to provide options to alter GraphQL's execution behavior in ways field arguments will not suffice, such as conditionally including or skipping a field. Directives provide this by describing additional information to the executor.""",
                "enumValues": None,
                "fields": [
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "name",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "String",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "description",
                        "type": {"kind": "SCALAR", "name": "String", "ofType": None},
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "locations",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "ENUM",
                                        "name": "__DirectiveLocation",
                                        "ofType": None,
                                    },
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": None,
                        "description": None,
                        "isDeprecated": False,
                        "name": "args",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "LIST",
                                "name": None,
                                "ofType": {
                                    "kind": "NON_NULL",
                                    "name": None,
                                    "ofType": {
                                        "kind": "OBJECT",
                                        "name": "__InputValue",
                                        "ofType": None,
                                    },
                                },
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": "Use `locations`.",
                        "description": None,
                        "isDeprecated": True,
                        "name": "onOperation",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": "Use `locations`.",
                        "description": None,
                        "isDeprecated": True,
                        "name": "onFragment",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    },
                    {
                        "args": [],
                        "deprecationReason": "Use `locations`.",
                        "description": None,
                        "isDeprecated": True,
                        "name": "onField",
                        "type": {
                            "kind": "NON_NULL",
                            "name": None,
                            "ofType": {
                                "kind": "SCALAR",
                                "name": "Boolean",
                                "ofType": None,
                            },
                        },
                    },
                ],
                "inputFields": None,
                "interfaces": [],
                "kind": "OBJECT",
                "name": "__Directive",
                "possibleTypes": None,
            },
            {
                "description": "A Directive can be adjacent to many parts of the GraphQL language, a __DirectiveLocation describes one such possible adjacencies.",
                "enumValues": [
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a query operation.",
                        "isDeprecated": False,
                        "name": "QUERY",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a mutation operation.",
                        "isDeprecated": False,
                        "name": "MUTATION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a subscription operation.",
                        "isDeprecated": False,
                        "name": "SUBSCRIPTION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a field.",
                        "isDeprecated": False,
                        "name": "FIELD",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a fragment definition.",
                        "isDeprecated": False,
                        "name": "FRAGMENT_DEFINITION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a fragment spread.",
                        "isDeprecated": False,
                        "name": "FRAGMENT_SPREAD",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an inline fragment.",
                        "isDeprecated": False,
                        "name": "INLINE_FRAGMENT",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a schema definition.",
                        "isDeprecated": False,
                        "name": "SCHEMA",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a scalar definition.",
                        "isDeprecated": False,
                        "name": "SCALAR",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an object definition.",
                        "isDeprecated": False,
                        "name": "OBJECT",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a field definition.",
                        "isDeprecated": False,
                        "name": "FIELD_DEFINITION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an argument definition.",
                        "isDeprecated": False,
                        "name": "ARGUMENT_DEFINITION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an interface definition.",
                        "isDeprecated": False,
                        "name": "INTERFACE",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to a union definition.",
                        "isDeprecated": False,
                        "name": "UNION",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an enum definition.",
                        "isDeprecated": False,
                        "name": "ENUM",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an enum value definition.",
                        "isDeprecated": False,
                        "name": "ENUM_VALUE",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an input object definition.",
                        "isDeprecated": False,
                        "name": "INPUT_OBJECT",
                    },
                    {
                        "deprecationReason": None,
                        "description": "Location adjacent to an input object field definition.",
                        "isDeprecated": False,
                        "name": "INPUT_FIELD_DEFINITION",
                    },
                ],
                "fields": None,
                "inputFields": None,
                "interfaces": None,
                "kind": "ENUM",
                "name": "__DirectiveLocation",
                "possibleTypes": None,
            },
        ],
    }
}
