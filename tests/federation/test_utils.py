from unittest.mock import Mock

from graphql.utilities import strip_ignored_characters as sic

from ariadne.contrib.federation import make_federated_schema
from ariadne.contrib.federation.utils import (
    add_typename_to_possible_return,
    gather_directives,
    get_entity_types,
    includes_directive,
    purge_schema_directives,
)


def test_purge_directives_retain_federation_directives():
    type_defs = """
        type Query {
            rootField: String
        }

        type Review @key(fields: "id") {
            id: ID!
            body: String
            author: User @provides(fields: "email")
            product: Product @provides(fields: "upc")
            link: String @tag(name: "href") @tag(name: "url")
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

    assert sic(purge_schema_directives(type_defs)) == sic(type_defs)


def test_purge_directives_retain_builtin_directives():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product {
            upc: ID!
            name: String
            label: String @deprecated(reason: "Use name instead")
        }
    """

    assert sic(purge_schema_directives(type_defs)) == sic(type_defs)


def test_purge_directives_remove_custom_directives():
    type_defs = """
        directive @custom on FIELD
        directive @other on FIELD

        directive @another on FIELD

        directive @plural repeatable on FIELD

        type Query {
            field1: String @custom
            field2: String @other
            field3: String @another
        }
    """

    assert sic(purge_schema_directives(type_defs)) == sic(
        """
            type Query {
                field1: String
                field2: String
                field3: String
            }
        """
    )


def test_purge_directives_remove_custom_directives_with_block_string_description():
    type_defs = '''
        """
        Any Description
        """
        directive @custom on FIELD
        
        type Query {
            rootField: String @custom
        }
    '''

    assert sic(purge_schema_directives(type_defs)) == sic(
        """
            type Query {
                rootField: String
            }
        """
    )


def test_purge_directives_remove_custom_directives_with_single_line_description():
    type_defs = """
        "Any Description"
        directive @custom on FIELD
        
        type Entity {
            field: String @custom
        }

        type Query {
            rootField: String @custom
        }
    """

    assert sic(purge_schema_directives(type_defs)) == sic(
        """
            type Entity {
                field: String
            }

            type Query {
                rootField: String
            }
        """
    )


def test_purge_directives_without_leading_whitespace():
    type_defs = "#\ndirective @custom on FIELD"

    assert sic(purge_schema_directives(type_defs)) == ""


def test_purge_directives_remove_custom_directives_from_interfaces():
    type_defs = """
        directive @custom on INTERFACE

        interface EntityInterface @custom {
            field: String
        }

        type Entity implements EntityInterface {
            field: String
        }

        type Query {
            rootField: Entity
        }
    """

    assert sic(purge_schema_directives(type_defs)) == sic(
        """
        interface EntityInterface {
            field: String
        }

        type Entity implements EntityInterface {
            field: String
        }

        type Query {
            rootField: Entity
        }
        """
    )


def test_purge_directives_remove_custom_directive_with_arguments():
    type_defs = """
        directive @custom(arg: String) on FIELD

        type Query {
            rootField: String @custom(arg: "value")
        }
    """

    assert sic(purge_schema_directives(type_defs)) == sic(
        """
            type Query {
                rootField: String
            }
        """
    )


def test_get_entity_types_with_key_directive():
    type_defs = """
        type Query {
            rootField: String
        }

        type Review {
            id: ID!
            body: String
            author: User
            product: Product
        }

        type User @key(fields: "email") @extends {
            email: String @external
        }

        type Product @key(fields: "upc") @extends {
            upc: ID! @external
            name: String
        }
    """

    schema = make_federated_schema(type_defs)
    entity_types_with_key_directive = get_entity_types(schema)

    assert len(entity_types_with_key_directive) == 2
    assert schema.get_type("User") in entity_types_with_key_directive
    assert schema.get_type("Product") in entity_types_with_key_directive


def test_includes_directive():
    type_defs = """
        directive @custom on INPUT_OBJECT

        type Query {
            rootField: String
        }

        input Input @custom {
            id: ID!
        }

        type Review {
            id: ID!
            body: String
            author: User
            product: Product
        }

        type User @key(fields: "email") @extends {
            email: String @external
        }

        type Product @key(fields: "upc") @extends {
            upc: ID! @external
            name: String
        }
    """

    schema = make_federated_schema(type_defs)

    assert not includes_directive(schema.get_type("Input"), "custom")
    assert not includes_directive(schema.get_type("Review"), "key")
    assert includes_directive(schema.get_type("User"), "key")
    assert includes_directive(schema.get_type("Product"), "key")


def test_gather_directives():
    type_defs = """
        type Query {
            rootField: String
        }

        type Product @key(fields: "upc") {
            upc: String! @external
            name: String
        }

        extend type Product @extends
    """

    schema = make_federated_schema(type_defs)
    product = schema.get_type("Product")
    directives = gather_directives(product)

    assert len(directives) == 2
    assert {d.name.value for d in directives} == {"key", "extends"}


def test_add_typename_to_dict():
    resolver_return = {"name": "Malbec"}

    add_typename_to_possible_return(resolver_return, "Product")

    assert resolver_return.get("__typename") == "Product"


def test_add_typename_to_object():
    resolver_return = Mock(name="Malbec")

    add_typename_to_possible_return(resolver_return, "Product")

    assert getattr(resolver_return, "_Mock__typename") == "Product"
