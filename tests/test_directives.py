import hashlib
from typing import Union

from graphql import default_field_resolver, graphql_sync
from graphql.type import (
    GraphQLField,
    GraphQLID,
    GraphQLInterfaceType,
    GraphQLObjectType,
)

from ariadne import (
    DirectiveType,
    QueryType,
    SchemaDirectiveVisitor,
    make_executable_schema,
)


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


def test_single_directive_without_args():
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
    upper_dir = DirectiveType("upper", UpperDirective)
    reverse_dir = DirectiveType("reverse", ReverseDirective)

    schema = make_executable_schema(type_defs, [query, upper_dir, reverse_dir])

    result = graphql_sync(schema, "{ test { node name }}")
    assert result.errors is None
    assert result.data == {"test": {"node": "CUSTOM", "name": "esacreppu"}}


def test_many_directives_without_args():
    type_defs = """
        directive @upper on FIELD_DEFINITION
        directive @reverse on FIELD_DEFINITION

        type Query {
          hello: String @upper @reverse
        }
    """

    query = QueryType()
    query.set_field("hello", lambda *_: "hello world")
    upper_dir = DirectiveType("upper", UpperDirective)
    reverse_dir = DirectiveType("reverse", ReverseDirective)

    schema = make_executable_schema(type_defs, [query, upper_dir, reverse_dir])

    result = graphql_sync(schema, "{ hello }")
    assert result.errors is None
    assert result.data == {"hello": "DLROW OLLEH"}


def test_unique_id_directive():
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
        def visit_object(self, type_: GraphQLObjectType) -> GraphQLObjectType:
            name, from_ = self.args.values()

            def _field_resolver(field, _):
                hash_ = hashlib.sha1(type_.name.encode())
                # breakpoint()
                for field_name in from_:
                    hash_.update(str(field[field_name]).encode())

                return hash_.hexdigest()

            type_.fields[name] = GraphQLField(
                description="Unique ID", type_=GraphQLID, resolve=_field_resolver
            )

    unique_id_dir = DirectiveType("uniqueID", UniqueIDDirective)

    query = QueryType()
    query.set_field("people", lambda *_: [{"personID": 1, "name": "Ben"}])
    query.set_field(
        "locations", lambda *_: [{"locationID": 1, "address": "140 10th St"}]
    )
    schema = make_executable_schema(type_defs, [query, unique_id_dir])

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
