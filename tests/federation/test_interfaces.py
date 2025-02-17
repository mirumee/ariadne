import pytest
from graphql import graphql_sync

from ariadne.contrib.federation import (
    FederatedInterfaceType,
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

            interface Product @key(fields: "upc") {
                upc: Int
                name: String
            }

            type Wine implements Product @key(fields: "upc") {
                upc: Int
                name: String
                content: Float
            }
        """
    )


def test_bind_interface_to_undefined_type_raises_error(schema):
    interface = FederatedInterfaceType("Test")
    with pytest.raises(ValueError):
        interface.bind_to_schema(schema)


def test_bind_interface_to_invalid_type_raises_error(schema):
    interface = FederatedInterfaceType("Date")
    with pytest.raises(ValueError):
        interface.bind_to_schema(schema)


def test_reference_resolver_can_be_set_using_decorator(schema):
    def resolve_result_type(*_):
        return "Wine"

    interface = FederatedInterfaceType("Product")
    interface.set_type_resolver(resolve_result_type)
    interface.reference_resolver()(lambda *_: {"name": "Malbec"})
    interface.bind_to_schema(schema)

    obj = FederatedObjectType("Wine")
    obj.bind_to_schema(schema)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Wine {
                        name
                    }
                }
            }
        """,
        variable_values={"representations": [{"__typename": "Wine", "upc": 1}]},
    )

    assert result.errors is None
    assert result.data["_entities"] == [{"name": "Malbec"}]


def test_reference_resolver_can_be_set_using_setter(schema):
    def resolve_result_type(*_):
        return "Wine"

    interface = FederatedInterfaceType("Product")
    interface.set_type_resolver(resolve_result_type)
    interface.reference_resolver(lambda *_: {"name": "Malbec"})
    interface.bind_to_schema(schema)

    obj = FederatedObjectType("Wine")
    obj.bind_to_schema(schema)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Wine {
                        name
                    }
                }
            }
        """,
        variable_values={"representations": [{"__typename": "Wine", "upc": 1}]},
    )

    assert result.errors is None
    assert result.data["_entities"] == [{"name": "Malbec"}]


def test_reference_resolver_can_be_set_on_both_interface_and_type(schema):
    def resolve_result_type(*_):
        return "Wine"

    interface = FederatedInterfaceType("Product")
    interface.set_type_resolver(resolve_result_type)
    interface.reference_resolver()(lambda *_: {"name": "Malbec"})
    interface.bind_to_schema(schema)

    obj = FederatedObjectType("Wine")
    obj.reference_resolver()(lambda *_: {"name": "Pinot"})
    obj.bind_to_schema(schema)

    result = graphql_sync(
        schema,
        """
            query GetEntities($representations: [_Any!]!) {
                _entities(representations: $representations) {
                    ... on Wine {
                        name
                    }
                }
            }
        """,
        variable_values={"representations": [{"__typename": "Wine", "upc": 1}]},
    )

    assert result.errors is None
    assert result.data["_entities"] == [{"name": "Pinot"}]
