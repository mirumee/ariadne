import hashlib
from typing import Union

from graphql import default_field_resolver, graphql_sync
from graphql.type import (
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLID,
    GraphQLInterfaceType,
    GraphQLObjectType,
)

from ariadne import QueryType, SchemaDirectiveVisitor, make_executable_schema


class UpperDirective(SchemaDirectiveVisitor):
    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        original_resolver = field.resolve or default_field_resolver

        def resolve_upper(obj, info, **kwargs):
            result = original_resolver(obj, info, **kwargs)
            return result.upper()

        field.resolve = resolve_upper
        return field


class ReverseDirective(SchemaDirectiveVisitor):
    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        original_resolver = field.resolve or default_field_resolver

        def resolve_reverse(obj, info, **kwargs):
            result = original_resolver(obj, info, **kwargs)
            return result[::-1]

        field.resolve = resolve_reverse
        return field


def test_field_definition_directive_replaces_field_resolver_with_custom_one():
    type_defs = """
        directive @upper on FIELD_DEFINITION
        directive @reverse on FIELD_DEFINITION

        type Query {
            test: Custom
        }

        type Custom {
            node: String @upper
            name: String @reverse
        }
    """

    query = QueryType()
    query.set_field("test", lambda *_: {"node": "custom", "name": "uppercase"})

    schema = make_executable_schema(
        type_defs,
        [query],
        directives={"upper": UpperDirective, "reverse": ReverseDirective},
    )

    result = graphql_sync(schema, "{ test { node name }}")
    assert result.errors is None
    assert result.data == {"test": {"node": "CUSTOM", "name": "esacreppu"}}


def test_multiple_field_definition_directives_replace_field_resolver_with_chainable_resolvers():
    type_defs = """
        directive @upper on FIELD_DEFINITION
        directive @reverse on FIELD_DEFINITION

        type Query {
          hello: String @upper @reverse
        }
    """

    query = QueryType()
    query.set_field("hello", lambda *_: "hello world")

    schema = make_executable_schema(
        type_defs,
        [query],
        directives={"upper": UpperDirective, "reverse": ReverseDirective},
    )

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "DLROW OLLEH"}


def test_can_implement_unique_id_directive():
    type_defs = """
    directive @uniqueID(name: String, from: [String]) on OBJECT

    type Query {
    people: [Person]
    locations: [Location]
    }

    type Person @uniqueID(name: "uid", from: ["personID"]) {
    personID: Int
    name: String
    }

    type Location @uniqueID(name: "uid", from: ["locationID"]) {
    locationID: Int
    address: String
    }"""

    class UniqueIDDirective(SchemaDirectiveVisitor):
        def visit_object(self, object_: GraphQLObjectType) -> GraphQLObjectType:
            name, from_ = self.args.values()

            def _field_resolver(field, _):
                hash_ = hashlib.sha1(object_.name.encode())
                for field_name in from_:
                    hash_.update(str(field[field_name]).encode())

                return hash_.hexdigest()

            object_.fields[name] = GraphQLField(
                description="Unique ID", type_=GraphQLID, resolve=_field_resolver
            )

    query = QueryType()
    query.set_field("people", lambda *_: [{"personID": 1, "name": "Ben"}])
    query.set_field(
        "locations", lambda *_: [{"locationID": 1, "address": "140 10th St"}]
    )
    schema = make_executable_schema(
        type_defs, [query], directives={"uniqueID": UniqueIDDirective}
    )

    result = graphql_sync(
        schema,
        """
        {
            people {
                uid
                personID
                name
            }
            locations {
                uid
                locationID
                address
            }
        }""",
    )
    assert result.errors is None
    assert result.data == {
        "locations": [
            {
                "uid": "c31b71e6e23a7ae527f94341da333590dd7cba96",
                "locationID": 1,
                "address": "140 10th St",
            }
        ],
        "people": [
            {
                "uid": "580a207c8e94f03b93a2b01217c3cc218490571a",
                "personID": 1,
                "name": "Ben",
            }
        ],
    }


def test_can_implement_remove_enum_values_directive():
    type_defs = """
        directive @remove(if: Boolean) on ENUM_VALUE

        type Query {
            age(unit: AgeUnit): Int
        }

        enum AgeUnit {
            DOG_YEARS
            TURTLE_YEARS @remove(if: true)
            PERSON_YEARS @remove(if: false)
        }"""

    class RemoveEnumDirective(SchemaDirectiveVisitor):
        def visit_enum_value(self, value: GraphQLEnumValue, enum_type: GraphQLEnumType):
            if self.args["if"]:
                return False
            return None

    schema = make_executable_schema(
        type_defs, directives={"remove": RemoveEnumDirective}
    )

    enum_type: GraphQLEnumType = schema.get_type("AgeUnit")
    assert list(enum_type.values.keys()) == ["DOG_YEARS", "PERSON_YEARS"]
