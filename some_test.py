from graphql import print_schema

from ariadne import make_executable_schema


typedefs = """
directive @example on OBJECT

type Query {
    test: Boolean
}

interface Node {
    edge: Boolean
    total: Int
}

extend type Query @example

interface OtherNode {
    total: Int
}

extend interface Node implements OtherNode
"""

schema = make_executable_schema(typedefs)
print(
    print_schema(schema)
)