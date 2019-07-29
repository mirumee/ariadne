from typing import Union

from graphql import default_field_resolver, graphql_sync
from graphql.type import GraphQLField, GraphQLInterfaceType, GraphQLObjectType

from ariadne import (
    DirectiveType,
    QueryType,
    SchemaDirectiveVisitor,
    make_executable_schema,
)


def test_directives():
    type_defs = """
        directive @upper on FIELD_DEFINITION
        directive @reverse on FIELD_DEFINITION

        type Query {
            test: Custom
        }

        type Custom {
            node: String @upper
            name: String @reverse @upper
        }
    """

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

            def resolve_upper(obj, info, **kwargs):
                result = original_resolver(obj, info, **kwargs)
                return result[::-1]

            field.resolve = resolve_upper
            return field

    query = QueryType()
    query.set_field("test", lambda *_: {"node": "custom", "name": "uppercase"})
    upper_dir = DirectiveType("upper", UpperDirective)
    reverse_dir = DirectiveType("reverse", ReverseDirective)

    schema = make_executable_schema(type_defs, [query, upper_dir, reverse_dir])

    result = graphql_sync(schema, "{ test { node name }}")
    assert result.errors is None
    assert result.data == {"test": {"node": "CUSTOM", "name": "ESACREPPU"}}
