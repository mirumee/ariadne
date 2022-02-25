# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_scalar_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('DateScalar class was defined with __schema__ containing invalid GraphQL type definition: ObjectTypeDefinitionNode (expected scalar)') tblen=3>")

snapshots['test_scalar_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'scalor\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_scalar_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('DateScalar class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_scalar_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('DateScalar class was defined with __schema__ containing more than one GraphQL definition (found: ScalarTypeDefinitionNode, ScalarTypeDefinitionNode)') tblen=3>")

snapshots['test_scalar_type_raises_error_when_defined_without_schema 1'] = GenericRepr("<ExceptionInfo TypeError('DateScalar class was defined without required __schema__ attribute') tblen=3>")
