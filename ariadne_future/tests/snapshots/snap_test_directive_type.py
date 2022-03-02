# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_directive_type_raises_attribute_error_when_defined_without_schema 1'] = GenericRepr('<ExceptionInfo AttributeError("type object \'ExampleDirective\' has no attribute \'__schema__\'") tblen=2>')

snapshots['test_directive_type_raises_attribute_error_when_defined_without_visitor 1'] = GenericRepr("<ExceptionInfo AttributeError('ExampleDirective class was defined without __visitor__ attribute') tblen=3>")

snapshots['test_directive_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleDirective class was defined with __schema__ without GraphQL directive') tblen=3>")

snapshots['test_directive_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'directivo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_directive_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('ExampleDirective class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_directive_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleDirective class was defined with __schema__ containing more than one GraphQL definition (found: DirectiveDefinitionNode, DirectiveDefinitionNode)') tblen=3>")
