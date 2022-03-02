# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_interface_type_raises_error_when_extended_dependency_is_wrong_type 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendExampleUnion requires \'Example\' to be GraphQL union but other type was provided in \'__requires__\'") tblen=3>')

snapshots['test_union_type_raises_attribute_error_when_defined_without_schema 1'] = GenericRepr('<ExceptionInfo AttributeError("type object \'ExampleUnion\' has no attribute \'__schema__\'") tblen=2>')

snapshots['test_union_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleUnion class was defined with __schema__ without GraphQL union') tblen=3>")

snapshots['test_union_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'unien\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_union_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('ExampleUnion class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_union_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleUnion class was defined with __schema__ containing more than one GraphQL definition (found: UnionTypeDefinitionNode, UnionTypeDefinitionNode)') tblen=3>")

snapshots['test_union_type_raises_error_when_defined_without_extended_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendExampleUnion class was defined without required GraphQL union definition for \'Result\' in __requires__") tblen=3>')

snapshots['test_union_type_raises_error_when_defined_without_member_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleUnion class was defined without required GraphQL definition for \'Comment\' in __requires__") tblen=3>')
