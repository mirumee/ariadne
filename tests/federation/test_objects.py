import pytest
from graphql import graphql_sync

from ariadne.contrib.federation import (
    FederatedObjectType,
    make_federated_schema,
)


@pytest.fixture
def schema():
    return make_federated_schema(
        """
        type Query {
            hello: String
        }

        scalar Date

        type Product @key(fields: "upc") {
            upc: Int
            name: String
        }
    """
    )


def test_bind_federated_object_type_to_undefined_type_raises_error(schema):
    obj = FederatedObjectType("Test")
    with pytest.raises(ValueError):
        obj.bind_to_schema(schema)


def test_bind_federated_object_type_to_invalid_type_raises_error(schema):
    obj = FederatedObjectType("Date")
    with pytest.raises(ValueError):
        obj.bind_to_schema(schema)


def test_reference_resolver_can_be_set_using_decorator(schema):
    obj = FederatedObjectType("Product")
    obj.reference_resolver()(lambda *_: {"name": "Malbec"})
    obj.bind_to_schema(schema)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        name
                    }
                }
            }
        """,
        variable_values={"representations": [{"__typename": "Product", "upc": 1}]},
    )

    assert result.errors is None
    assert result.data["_entities"] == [{"name": "Malbec"}]


def test_reference_resolver_can_be_set_using_setter(schema):
    obj = FederatedObjectType("Product")
    obj.reference_resolver(lambda *_: {"name": "Malbec"})
    obj.bind_to_schema(schema)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Product {
                        name
                    }
                }
            }
        """,
        variable_values={"representations": [{"__typename": "Product", "upc": 1}]},
    )

    assert result.errors is None
    assert result.data["_entities"] == [{"name": "Malbec"}]
