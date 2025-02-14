from graphql.type import GraphQLObjectType, GraphQLSchema

from ariadne import make_executable_schema
from ariadne.schema_visitor import SchemaVisitor, visit_schema

TYPE_DEFS = """
directive @schemaDirective(role: String) on SCHEMA
directive @queryTypeDirective on OBJECT
directive @queryFieldDirective on FIELD_DEFINITION
directive @enumTypeDirective on ENUM
directive @enumValueDirective on ENUM_VALUE
directive @dateDirective(tz: String) on SCALAR
directive @interfaceDirective on INTERFACE
directive @interfaceFieldDirective on FIELD_DEFINITION
directive @inputTypeDirective on INPUT_OBJECT
directive @inputFieldDirective on INPUT_FIELD_DEFINITION
directive @mutationTypeDirective on OBJECT
directive @mutationArgumentDirective on ARGUMENT_DEFINITION
directive @mutationMethodDirective on FIELD_DEFINITION
directive @objectTypeDirective on OBJECT
directive @objectFieldDirective on FIELD_DEFINITION
directive @unionDirective on UNION

schema @schemaDirective(role: "admin") {
  query: Query
  mutation: Mutation
}

type Query @queryTypeDirective {
  people: [Person] @queryFieldDirective
}

enum Gender @enumTypeDirective {
  NONBINARY @enumValueDirective
  FEMALE
  MALE
}

scalar Date @dateDirective(tz: "utc")

interface Named @interfaceDirective {
  name: String! @interfaceFieldDirective
}

input PersonInput @inputTypeDirective {
  name: String! @inputFieldDirective
  gender: Gender
}

type Mutation @mutationTypeDirective {
  addPerson(
    input: PersonInput @mutationArgumentDirective
  ): Person @mutationMethodDirective
}

type Person implements Named @objectTypeDirective {
  id: ID! @objectFieldDirective
  name: String!
}

union WhateverUnion @unionDirective = Person | Query | Mutation
"""


def test_visitor():
    class SimpleVisitor(SchemaVisitor):
        visit_count = 0
        names: list[str] = []

        def __init__(self, schema: GraphQLSchema):
            self.schema = schema

        def visit(self):
            visit_schema(self.schema, lambda *_: [self])

        def visit_object(self, object_: GraphQLObjectType):
            assert self.schema.get_type(object_.name) == object_
            self.names.append(object_.name)

    schema = make_executable_schema(TYPE_DEFS)

    visitor = SimpleVisitor(schema)
    visitor.visit()
    assert sorted(visitor.names) == ["Mutation", "Person", "Query"]


def test_can_check_if_a_visitor_method_is_implemented():
    class Visitor(SchemaVisitor):
        def not_visitor_method(self):
            return

        def visit_object(self, object_: GraphQLObjectType):
            return object_

    assert Visitor.implements_visitor_method("not_visitor_method") is False

    assert Visitor.implements_visitor_method("visit_object") is True

    assert Visitor.implements_visitor_method("visit_input_field_definition") is False

    assert Visitor.implements_visitor_method("visit_bogus_type") is False
