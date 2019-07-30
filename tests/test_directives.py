from typing import Union

from graphql import default_field_resolver, graphql_sync
from graphql.type import GraphQLField, GraphQLInterfaceType, GraphQLObjectType

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
