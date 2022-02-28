# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_union_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleUnion class was defined with __schema__ containing GraphQL definition for \'ScalarTypeDefinitionNode\' (expected \'union\')") tblen=3>')

snapshots['test_union_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'unien\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_union_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('ExampleUnion class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_union_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleUnion class was defined with __schema__ containing more than one GraphQL definition (found: UnionTypeDefinitionNode, UnionTypeDefinitionNode)') tblen=3>")

snapshots['test_union_type_raises_error_when_defined_without_member_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleUnion class was defined without required GraphQL type definition for \'Comment\' in __requires__") tblen=3>')

snapshots['test_union_type_raises_error_when_defined_without_schema 1'] = GenericRepr("<ExceptionInfo TypeError('ExampleUnion class was defined without required __schema__ attribute') tblen=3>")
