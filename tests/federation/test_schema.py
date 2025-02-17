from unittest.mock import Mock

import pytest
from graphql import graphql, graphql_sync
from graphql.utilities import strip_ignored_characters as sic
from graphql.utilities.print_schema import (
    print_interface,
    print_object,
    print_union,
)

from ariadne.contrib.federation import (
    FederatedInterfaceType,
    FederatedObjectType,
    make_federated_schema,
)


def test_federation_one_schema_mark_type_tags():
    type_defs = """
        type Query

        directive @tag(name: String!) repeatable on
            | FIELD_DEFINITION
            | INTERFACE
            | OBJECT
            | UNION
            | ARGUMENT_DEFINITION
            | SCALAR
            | ENUM
            | ENUM_VALUE
            | INPUT_OBJECT
            | INPUT_FIELD_DEFINITION

        type Product @tag(name: "test") {
            upc: String!
            name: String
            price: Int @tag(name: "test2")
        }
    """
    product = FederatedObjectType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
            type Product {
                upc: String!
                name: String
                price: Int
            }
        """
    )


def test_federation_one_schema_mark_type_repeated_tags():
    type_defs = """
        type Query

        directive @tag(name: String!) repeatable on
            | FIELD_DEFINITION
            | INTERFACE
            | OBJECT
            | UNION
            | ARGUMENT_DEFINITION
            | SCALAR
            | ENUM
            | ENUM_VALUE
            | INPUT_OBJECT
            | INPUT_FIELD_DEFINITION

        type Product @tag(name: "test") @tag(name: "test3") {
            upc: String!
            name: String
            price: Int @tag(name: "test2") @tag(name: "test4")
        }
    """
    product = FederatedObjectType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
            type Product {
                upc: String!
                name: String
                price: Int
            }
        """
    )


def test_federated_schema_mark_type_with_key():
    type_defs = """
        type Query

        type Product @key(fields: "upc") {
            upc: String!
            name: String
            price: Int
        }
    """

    product = FederatedObjectType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
            type Product {
                upc: String!
                name: String
                price: Int
            }
        """
    )

    assert sic(print_union(schema.get_type("_Entity"))) == sic(
        """
            union _Entity = Product
        """
    )


def test_federated_schema_mark_type_with_key_split_type_defs():
    query_type_defs = """
        type Query
    """

    product_type_defs = """
        type Product @key(fields: "upc") {
            upc: String!
            name: String
            price: Int
        }
    """

    product = FederatedObjectType("Product")
    schema = make_federated_schema(
        [query_type_defs, product_type_defs],
        product,
    )

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
            type Product {
                upc: String!
                name: String
                price: Int
            }
        """
    )

    assert sic(print_union(schema.get_type("_Entity"))) == sic(
        """
            union _Entity = Product
        """
    )


def test_federated_schema_mark_type_with_multiple_keys():
    type_defs = """
        type Query

        type Product @key(fields: "upc sku") {
            upc: String!
            sku: String!
            name: String
            price: Int
        }
    """

    product = FederatedObjectType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
        type Product {
            upc: String!
            sku: String!
            name: String
            price: Int
        }
    """
    )

    assert sic(print_union(schema.get_type("_Entity"))) == sic(
        """
            union _Entity = Product
        """
    )


def test_federated_schema_not_mark_type_with_no_keys():
    type_defs = """
        type Query

        type Product {
            upc: String!
            name: String
            price: Int
        }
    """

    product = FederatedObjectType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
            type Product {
                upc: String!
                name: String
                price: Int
            }
        """
    )

    assert schema.get_type("_Entity") is None


def test_federated_schema_type_with_multiple_keys():
    type_defs = """
        type Query
        type Product @key(fields: "upc") @key(fields: "sku") {
            upc: String!
            sku: String!
            price: String
        }
    """
    FederatedObjectType("Product")
    schema = make_federated_schema(type_defs)

    assert sic(print_object(schema.get_type("Product"))) == sic(
        """
            type Product {
                upc: String!
                sku: String!
                price: String
            }
        """
    )


def test_federated_schema_mark_interface_with_key():
    type_defs = """
        type Query

        interface Product @key(fields: "upc") {
            upc: String!
            name: String
            price: Int
        }
    """

    product = FederatedInterfaceType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_interface(schema.get_type("Product"))) == sic(
        """
            interface Product {
                upc: String!
                name: String
                price: Int
            }
        """
    )

    assert schema.get_type("_Entity") is None


def test_federated_schema_mark_interface_with_multiple_keys():
    type_defs = """
        type Query

        interface Product @key(fields: "upc sku") {
            upc: String!
            sku: String!
            name: String
            price: Int
        }
    """

    product = FederatedInterfaceType("Product")
    schema = make_federated_schema(type_defs, product)

    assert sic(print_interface(schema.get_type("Product"))) == sic(
        """
            interface Product {
                upc: String!
                sku: String!
                name: String
                price: Int
            }
        """
    )

    assert schema.get_type("_Entity") is None


def test_federated_schema_augment_root_query_with_type_key():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: ID!
        }
    """

    schema = make_federated_schema(type_defs)

    assert sic(print_object(schema.get_type("Query"))) == sic(
        """
            type Query {
                rootField: String
                _service: _Service!
                _entities(representations: [_Any!]!): [_Entity]!
            }
        """
    )


def test_federated_schema_augment_root_query_with_interface_key():
    type_defs = """
        type Query {
            rootField: String
        }

        interface Product @key(fields: "upc") {
            upc: ID!
        }
    """

    schema = make_federated_schema(type_defs)

    assert sic(print_object(schema.get_type("Query"))) == sic(
        """
            type Query {
                rootField: String
                _service: _Service!
            }
        """
    )


def test_federated_schema_augment_root_query_with_no_keys():
    type_defs = """
        type Query {
            rootField: String
        }
    """

    schema = make_federated_schema(type_defs)

    assert sic(print_object(schema.get_type("Query"))) == sic(
        """
            type Query {
                rootField: String
                _service: _Service!
            }
        """
    )


def test_federated_schema_execute_reference_resolver():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: Int
            name: String
        }

        type User @key(fields: "id") {
            firstName: String
        }
    """

    product = FederatedObjectType("Product")

    @product.reference_resolver()
    def product_reference_resolver(_obj, _info, reference):
        assert reference["upc"] == 1
        return {"name": "Apollo Gateway"}

    user = FederatedObjectType("User")

    @user.reference_resolver()
    def user_reference_resolver(_obj, _info, reference):
        assert reference["id"] == 1
        return Mock(firstName="James")

    schema = make_federated_schema(type_defs, [product, user])

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        __typename
                        name
                    }
                    ... on User {
                        __typename
                        firstName
                    }
                }
            }
        """,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "upc": 1,
                },
                {
                    "__typename": "User",
                    "id": 1,
                },
            ],
        },
    )

    assert result.errors is None
    assert result.data["_entities"][0]["__typename"] == "Product"
    assert result.data["_entities"][0]["name"] == "Apollo Gateway"
    assert result.data["_entities"][1]["__typename"] == "User"
    assert result.data["_entities"][1]["firstName"] == "James"


@pytest.mark.parametrize("primary_key", ["sku", "upc"])
def test_federated_schema_execute_reference_resolver_with_multiple_keys(primary_key):
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") @key(fields: "sku") {
            upc: Int!
            sku: Int!
            name: String
        }

        type User @key(fields: "id") {
            firstName: String
        }
    """

    product = FederatedObjectType("Product")

    @product.reference_resolver()
    def product_reference_resolver(_obj, _info, reference):
        assert reference[primary_key] == 1
        return {"name": "Apollo Gateway"}

    user = FederatedObjectType("User")

    @user.reference_resolver()
    def user_reference_resolver(_obj, _info, reference):
        assert reference["id"] == 1
        return Mock(firstName="James")

    schema = make_federated_schema(type_defs, [product, user])

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        __typename
                        name
                    }
                    ... on User {
                        __typename
                        firstName
                    }
                }
            }
        """,
        variable_values={
            "representations": [
                {"__typename": "Product", primary_key: 1},
                {
                    "__typename": "User",
                    "id": 1,
                },
            ],
        },
    )
    assert result.errors is None
    assert result.data["_entities"][0]["__typename"] == "Product"
    assert result.data["_entities"][0]["name"] == "Apollo Gateway"
    assert result.data["_entities"][1]["__typename"] == "User"
    assert result.data["_entities"][1]["firstName"] == "James"


@pytest.mark.asyncio
async def test_federated_schema_execute_async_reference_resolver():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: Int
            name: String
        }

        type User @key(fields: "id") {
            firstName: String
        }
    """

    product = FederatedObjectType("Product")

    @product.reference_resolver()
    async def product_reference_resolver(_obj, _info, reference):
        assert reference["upc"] == 1
        return {"name": "Apollo Gateway"}

    user = FederatedObjectType("User")

    @user.reference_resolver()
    async def user_reference_resolver(_obj, _info, reference):
        assert reference["id"] == 1
        return Mock(firstName="James")

    schema = make_federated_schema(type_defs, [product, user])

    result = await graphql(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        __typename
                        name
                    }
                    ... on User {
                        __typename
                        firstName
                    }
                }
            }
        """,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "upc": 1,
                },
                {
                    "__typename": "User",
                    "id": 1,
                },
            ],
        },
    )

    assert result.errors is None
    assert result.data["_entities"][0]["__typename"] == "Product"
    assert result.data["_entities"][0]["name"] == "Apollo Gateway"
    assert result.data["_entities"][1]["__typename"] == "User"
    assert result.data["_entities"][1]["firstName"] == "James"


def test_federated_schema_execute_default_reference_resolver():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: Int
            name: String
        }
    """

    schema = make_federated_schema(type_defs)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        upc
                        name
                    }
                }
            }
        """,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "upc": 1,
                    "name": "Apollo Gateway",
                },
            ],
        },
    )

    assert result.errors is None
    assert result.data["_entities"][0]["name"] == "Apollo Gateway"


def test_federated_schema_execute_reference_resolver_that_returns_none():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: Int
            name: String
        }
    """

    product = FederatedObjectType("Product")

    @product.reference_resolver()
    def product_reference_resolver(_obj, _info, reference):
        assert reference["upc"] == 1
        # return None

    schema = make_federated_schema(type_defs, product)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        __typename
                        name
                    }
                }
            }
        """,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "upc": 1,
                },
            ],
        },
    )

    assert result.errors is None
    assert result.data["_entities"][0] is None


def test_federated_schema_raises_error_on_missing_type():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: String! @external
            name: String
        }
    """

    schema = make_federated_schema(type_defs)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        upc
                    }
                }
            }
        """,
        variable_values={
            "representations": [
                {
                    "__typename": "ProductWrongSpelling",
                    "id": 1,
                },
            ],
        },
    )

    assert result.errors is not None


def test_federated_schema_query_service_with_key():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: String!
            name: String
            price: Int
        }
    """

    schema = make_federated_schema(type_defs)

    result = graphql_sync(
        schema,
        """
            query GetServiceDetails {
                _service {
                    sdl
                }
            }
        """,
    )

    assert result.errors is None
    assert sic(result.data["_service"]["sdl"]) == sic(
        """
            type Query {
                rootField: String
            }

            type Product @key(fields: "upc") {
                upc: String!
                name: String
                price: Int
            }
        """
    )


def test_federated_schema_query_service_with_multiple_keys():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc sku") {
            upc: String!
            sku: String!
            name: String
            price: Int
        }
    """

    schema = make_federated_schema(type_defs)

    result = graphql_sync(
        schema,
        """
            query GetServiceDetails {
                _service {
                    sdl
                }
            }
        """,
    )

    assert result.errors is None
    assert sic(result.data["_service"]["sdl"]) == sic(
        """
            type Query {
                rootField: String
            }

            type Product @key(fields: "upc sku") {
                upc: String!
                sku: String!
                name: String
                price: Int
            }
        """
    )


def test_federated_schema_query_service_provide_federation_directives():
    type_defs = """
        type Query {
            rootField: String
        }

        type Review @key(fields: "id") {
            id: ID!
            body: String
            author: User @provides(fields: "email")
            product: Product @provides(fields: "upc")
        }

        type User @key(fields: "email") @extends {
            email: String @external
            reviews: [Review]
        }

        type Product @key(fields: "upc") @extends {
            upc: String @external
            reviews: [Review]
        }
    """

    schema = make_federated_schema(type_defs)

    result = graphql_sync(
        schema,
        """
            query GetServiceDetails {
                _service {
                    sdl
                }
            }
        """,
    )

    assert result.errors is None
    assert sic(result.data["_service"]["sdl"]) == sic(
        """
            type Query {
                rootField: String
            }

            type Review @key(fields: "id") {
                id: ID!
                body: String
                author: User @provides(fields: "email")
                product: Product @provides(fields: "upc")
            }

            type User @key(fields: "email") @extends {
                email: String @external
                reviews: [Review]
            }

            type Product @key(fields: "upc") @extends {
                upc: String @external
                reviews: [Review]
            }
        """
    )


def test_federated_schema_query_service_ignore_custom_directives():
    type_defs = """
        directive @custom on FIELD

        type Query {
            rootField: String
        }

        type User @key(fields: "email") @extends {
            email: String @external
        }
    """

    schema = make_federated_schema(type_defs)

    result = graphql_sync(
        schema,
        """
            query GetServiceDetails {
                _service {
                    sdl
                }
            }
        """,
    )

    assert result.errors is None
    assert sic(result.data["_service"]["sdl"]) == sic(
        """
            type Query {
                rootField: String
            }

            type User @key(fields: "email") @extends {
                email: String @external
            }
        """
    )


def test_federated_schema_without_query_is_valid():
    type_defs = """
    type Product @key(fields: "upc") {
        upc: String!
        name: String
        price: Int
        weight: Int
    }
    """

    schema = make_federated_schema(type_defs)
    result = graphql_sync(
        schema,
        """
            query GetServiceDetails {
                _service {
                    sdl
                }
            }
        """,
    )

    assert result.errors is None
    assert sic(result.data["_service"]["sdl"]) == sic(type_defs)
