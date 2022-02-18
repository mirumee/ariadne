# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_object_type_raises_error_when_declared_with_empty_type 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was declared with __schema__ containing empty GraphQL type definition') tblen=3>")

snapshots['test_object_type_raises_error_when_declared_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was declared with __schema__ without GraphQL type definition (found: ScalarTypeDefinitionNode)') tblen=3>")

snapshots['test_object_type_raises_error_when_declared_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_object_type_raises_error_when_declared_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UserType class was declared with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_object_type_raises_error_when_declared_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was declared with __schema__ containing more than one definition (found: ObjectTypeDefinitionNode, ObjectTypeDefinitionNode)') tblen=3>")

snapshots['test_object_type_raises_error_when_declared_without_extended_dependency 1'] = GenericRepr("<ExceptionInfo ValueError('ExtendUserType class was declared with __schema__ extending unknown dependency: User') tblen=2>")

snapshots['test_object_type_raises_error_when_declared_without_schema 1'] = GenericRepr("<ExceptionInfo TypeError('UserType class was declared without required __schema__ attribute') tblen=3>")

snapshots['test_object_type_raises_error_when_declared_without_type_dependency 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was declared with __schema__ containing unknown dependency: Group') tblen=2>")
