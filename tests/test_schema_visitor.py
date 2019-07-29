from typing import List

from graphql.type import GraphQLObjectType, GraphQLSchema

from ariadne import make_executable_schema
from ariadne.schema_visitor import SchemaVisitor, visit_schema

typeDefs = """
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
        visitCount = 0
        names: List[str] = []

        def __init__(self, schema: GraphQLSchema):
            self.schema = schema

        def visit(self):
            visit_schema(self.schema, lambda *_: [self])

        def visit_object(self, object_: GraphQLObjectType):
            assert self.schema.get_type(object_.name) == object
            self.names.append(object_.name)

    schema = make_executable_schema(typeDefs)

    visitor = SimpleVisitor(schema)
    visitor.visit()
    assert sorted(visitor.names) == ["Mutation", "Person", "Query"]
