import pytest
from graphql import GraphQLError, default_field_resolver, graphql_sync

from ariadne import SchemaDirectiveVisitor

from ..directive_type import DirectiveType
from ..executable_schema import make_executable_schema
from ..object_type import ObjectType


def test_directive_type_raises_error_when_defined_without_schema(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class ExampleDirective(DirectiveType):
            pass

    snapshot.assert_match(err)


def test_directive_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class ExampleDirective(DirectiveType):
            pass

    snapshot.assert_match(err)


def test_directive_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class ExampleDirective(DirectiveType):
            __schema__ = "directivo @example on FIELD_DEFINITION"

    snapshot.assert_match(err)


def test_directive_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleDirective(DirectiveType):
            __schema__ = "scalar example"

    snapshot.assert_match(err)


def test_directive_type_raises_error_when_defined_with_multiple_types_schema(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleDirective(DirectiveType):
            __schema__ = """
            directive @example on FIELD_DEFINITION

            directive @other on OBJECT
            """

    snapshot.assert_match(err)


def test_directive_type_raises_error_when_defined_without_visitor(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleDirective(DirectiveType):
            __schema__ = "directive @example on FIELD_DEFINITION"

    snapshot.assert_match(err)


class ExampleSchemaVisitor(SchemaDirectiveVisitor):
    def visit_field_definition(self, field, object_type):
        original_resolver = field.resolve or default_field_resolver

        def resolve_prefixed_value(obj, info, **kwargs):
            result = original_resolver(obj, info, **kwargs)
            if result:
                return f"PREFIX: {result}"
            return result

        field.resolve = resolve_prefixed_value
        return field


def test_directive_type_extracts_graphql_name():
    class ExampleDirective(DirectiveType):
        __schema__ = "directive @example on FIELD_DEFINITION"
        __visitor__ = ExampleSchemaVisitor

    assert ExampleDirective.graphql_name == "example"


def test_directive_is_set_on_field():
    class ExampleDirective(DirectiveType):
        __schema__ = "directive @example on FIELD_DEFINITION"
        __visitor__ = ExampleSchemaVisitor

    class QueryType(ObjectType):
        __schema__ = """
        type Query {
            field: String! @example
        }
        """
        __requires__ = [ExampleDirective]

    schema = make_executable_schema(QueryType)
    result = graphql_sync(schema, "{ field }", root_value={"field": "test"})
    assert result.data == {"field": "PREFIX: test"}
