# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_definition_parser_raises_error_schema_str_contains_multiple_types 1'] = GenericRepr("<ExceptionInfo ValueError('MyType class was defined with __schema__ containing more than one GraphQL definition (found: ObjectTypeDefinitionNode, ObjectTypeDefinitionNode)') tblen=2>")

snapshots['test_definition_parser_raises_error_when_schema_str_has_invalid_syntax 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=6>')

snapshots['test_definition_parser_raises_error_when_schema_type_is_invalid 1'] = GenericRepr("<ExceptionInfo TypeError('MyType class was defined with __schema__ of invalid type: bool') tblen=2>")

snapshots['test_parse_definition_raises_error_schema_str_contains_multiple_types 1'] = GenericRepr("<ExceptionInfo ValueError('MyType class was defined with __schema__ containing more than one GraphQL definition (found: ObjectTypeDefinitionNode, ObjectTypeDefinitionNode)') tblen=2>")

snapshots['test_parse_definition_raises_error_when_schema_is_none 1'] = GenericRepr("<ExceptionInfo TypeError('MyType class was defined without required __schema__ attribute') tblen=2>")

snapshots['test_parse_definition_raises_error_when_schema_str_has_invalid_syntax 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=6>')

snapshots['test_parse_definition_raises_error_when_schema_type_is_invalid 1'] = GenericRepr("<ExceptionInfo TypeError('MyType class was defined with __schema__ of invalid type: bool') tblen=2>")
