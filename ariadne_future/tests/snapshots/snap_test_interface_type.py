# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_interface_type_raises_error_when_defined_with_alias_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleInterface class was defined with aliases for fields not in GraphQL type: joinedDate') tblen=3>")

snapshots['test_interface_type_raises_error_when_defined_with_empty_type 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleInterface class was defined with __schema__ containing empty GraphQL interface definition') tblen=3>")

snapshots['test_interface_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleInterface class was defined with __schema__ containing GraphQL definition for \'ObjectTypeDefinitionNode\' (expected \'interface\')") tblen=3>')

snapshots['test_interface_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'interfaco\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_interface_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('ExampleInterface class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_interface_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleInterface class was defined with __schema__ containing more than one GraphQL definition (found: InterfaceTypeDefinitionNode, InterfaceTypeDefinitionNode)') tblen=3>")

snapshots['test_interface_type_raises_error_when_defined_with_resolver_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('ExampleInterface class was defined with resolvers for fields not in GraphQL type: resolve_group') tblen=3>")

snapshots['test_interface_type_raises_error_when_defined_without_argument_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleInterface class was defined without required GraphQL type definition for \'UserInput\' in __requires__") tblen=3>')

snapshots['test_interface_type_raises_error_when_defined_without_extended_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendExampleInterface class was defined with __schema__ containing GraphQL definition for \'InterfaceTypeExtensionNode\' (expected \'type\')") tblen=3>')

snapshots['test_interface_type_raises_error_when_defined_without_return_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleInterface class was defined without required GraphQL type definition for \'Group\' in __requires__") tblen=3>')

snapshots['test_interface_type_raises_error_when_defined_without_schema 1'] = GenericRepr("<ExceptionInfo TypeError('ExampleInterface class was defined without required __schema__ attribute') tblen=3>")

snapshots['test_interface_type_raises_error_when_extended_dependency_is_wrong_type 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleInterface requires \'Example\' to be GraphQL interface but other type was provided in \'__requires__\'") tblen=3>')
