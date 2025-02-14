from graphql import graphql_sync
from graphql.utilities import strip_ignored_characters as sic

from ariadne.contrib.federation import (
    make_federated_schema,
)


def test_federation_2_0_version_is_detected_in_schema():
    type_defs = """
        extend schema @link(
            url: "https://specs.apollo.dev/federation/v2.0", 
            import: [
                "@key",
                "@shareable",
                "@provides",
                "@external",
                "@tag",
                "@extends",
                "@override"
            ]
        )

        type Product @key(fields: "upc") {
            upc: String!
            name: String
            price: Int
            weight: Int
        }

        type User @key(fields: "email") @extends {
            email: ID! @external
            name: String @override(from:"users")
            totalProductsCreated: Int @external
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


def test_federation_2_1_version_is_detected_in_schema():
    type_defs = """
        extend schema @link(
            url: "https://specs.apollo.dev/federation/v2.1",
            import: ["@key",
            "@shareable",
            "@provides",
            "@external",
            "@tag",
            "@extends",
            "@override"])

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


def test_federation_2_2_version_is_detected_in_schema():
    type_defs = """
        extend schema @link(
            url: "https://specs.apollo.dev/federation/v2.2",
            import: [
                "@key",
                "@shareable",
                "@provides",
                "@external",
                "@tag",
                "@extends",
                "@override"
            ]
        )

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


def test_federated_schema_query_service_interface_object_federation_directive():
    type_defs = """
        extend schema
            @link(
                url: "https://specs.apollo.dev/federation/v2.3",
                import: [
                    "@key",
                    "@shareable",
                    "@provides",
                    "@external",
                    "@tag",
                    "@extends",
                    "@override",
                    "@interfaceObject"
                ]
            )

        type Query {
            rootField: Review
        }

        type Review @interfaceObject @key(fields: "id") {
            id: ID!
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
            extend schema
                @link(
                    url: "https://specs.apollo.dev/federation/v2.3",
                    import: [
                        "@key",
                        "@shareable",
                        "@provides",
                        "@external",
                        "@tag",
                        "@extends",
                        "@override",
                        "@interfaceObject"
                    ]
                )

            type Query {
                rootField: Review
            }

            type Review @interfaceObject @key(fields: "id") {
                id: ID!
            }
        """
    )


def test_federation_2_4_version_is_detected_in_schema():
    type_defs = """
        extend schema
            @link(
                url: "https://specs.apollo.dev/federation/v2.4",
                import: [
                    "@key",
                    "@shareable",
                    "@provides",
                    "@external",
                    "@tag",
                    "@extends",
                    "@override",
                    "@interfaceObject"
                ]
            )

        type Query {
            rootField: Review
        }

        type Review @interfaceObject @key(fields: "id") {
            id: ID!
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
            extend schema
                @link(
                    url: "https://specs.apollo.dev/federation/v2.4",
                    import: [
                        "@key",
                        "@shareable",
                        "@provides",
                        "@external",
                        "@tag",
                        "@extends",
                        "@override",
                        "@interfaceObject"
                    ]
                )

            type Query {
                rootField: Review
            }

            type Review @interfaceObject @key(fields: "id") {
                id: ID!
            }
        """
    )


def test_federation_2_5_version_is_detected_in_schema():
    type_defs = """
        extend schema
            @link(
                url: "https://specs.apollo.dev/federation/v2.5",
                import: [
                    "@key",
                    "@shareable",
                    "@provides",
                    "@external",
                    "@tag",
                    "@extends",
                    "@override",
                    "@interfaceObject",
                    "@authenticated",
                    "@requiresScopes",

                ]
            )

        type Query {
            rootField: Review
        }

        type Review
            @interfaceObject
            @key(fields: "id")
            @authenticated
            @requiresScopes(scopes: [["read:review"]]) {
            id: ID!
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
            extend schema
                @link(
                    url: "https://specs.apollo.dev/federation/v2.5",
                    import: [
                        "@key",
                        "@shareable",
                        "@provides",
                        "@external",
                        "@tag",
                        "@extends",
                        "@override",
                        "@interfaceObject"
                        "@authenticated",
                        "@requiresScopes",
                    ]
                )

            type Query {
                rootField: Review
            }

            type Review
                @interfaceObject @key(fields: "id")
                @authenticated
                @requiresScopes(scopes: [["read:review"]]) {
                id: ID!
            }
        """
    )


def test_federation_2_6_version_is_detected_in_schema():
    type_defs = """
        extend schema
            @link(
                url: "https://specs.apollo.dev/federation/v2.6",
                import: [
                    "@key",
                    "@shareable",
                    "@provides",
                    "@external",
                    "@tag",
                    "@extends",
                    "@override",
                    "@interfaceObject",
                    "@authenticated",
                    "@requiresScopes",

                ]
            )

        type Query {
            rootField: Review
        }

        type Review
            @interfaceObject
            @key(fields: "id")
            @authenticated
            @requiresScopes(scopes: [["read:review"]])
            @policy(policies: [["role:admin"]])
             {
            id: ID!
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
            extend schema
                @link(
                    url: "https://specs.apollo.dev/federation/v2.6",
                    import: [
                        "@key",
                        "@shareable",
                        "@provides",
                        "@external",
                        "@tag",
                        "@extends",
                        "@override",
                        "@interfaceObject"
                        "@authenticated",
                        "@requiresScopes",
                    ]
                )

            type Query {
                rootField: Review
            }

            type Review
                @interfaceObject
                @key(fields: "id")
                @authenticated
                @requiresScopes(scopes: [["read:review"]])
                @policy(policies: [["role:admin"]])
                {
                id: ID!
            }
        """
    )


def test_federation_version_not_supported_is_detected_in_schema():
    type_defs = """
        extend schema
            @link(
                url: "https://specs.apollo.dev/federation/v2.25",
                import: [
                    "@key",
                    "@shareable",
                    "@provides",
                    "@external",
                    "@tag",
                    "@extends",
                    "@override",
                    "@interfaceObject",
                    "@authenticated",
                    "@requiresScopes",

                ]
            )

        type Query {
            rootField: Review
        }

        type Review
            @interfaceObject
            @key(fields: "id")
            @authenticated
            @requiresScopes(scopes: [["read:review"]])
            @policy(policies: [["role:admin"]])
             {
            id: ID!
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
            extend schema
                @link(
                    url: "https://specs.apollo.dev/federation/v2.25",
                    import: [
                        "@key",
                        "@shareable",
                        "@provides",
                        "@external",
                        "@tag",
                        "@extends",
                        "@override",
                        "@interfaceObject"
                        "@authenticated",
                        "@requiresScopes",
                    ]
                )

            type Query {
                rootField: Review
            }

            type Review
                @interfaceObject
                @key(fields: "id")
                @authenticated
                @requiresScopes(scopes: [["read:review"]])
                @policy(policies: [["role:admin"]])
                {
                id: ID!
            }
        """
    )
