# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_object_type_raises_error_when_defined_with_empty_type 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with __schema__ containing empty GraphQL type definition') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with __schema__ containing invalid GraphQL type definition: ScalarTypeDefinitionNode (expected type)') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_object_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UserType class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with __schema__ containing more than one GraphQL definition (found: ObjectTypeDefinitionNode, ObjectTypeDefinitionNode)') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_without_extended_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendUserType clfgraphql_typeass was defined without required GraphQL type definition for \'User\' in __requires__") tblen=3>')

snapshots['test_object_type_raises_error_when_defined_without_schema 1'] = GenericRepr("<ExceptionInfo TypeError('UserType class was defined without required __schema__ attribute') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_without_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("UserType class was defined without required GraphQL type definition for \'Group\' in __requires__") tblen=3>')
