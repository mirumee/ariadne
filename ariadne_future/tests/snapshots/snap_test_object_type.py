# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_object_type_raises_attribute_error_when_defined_without_schema 1'] = GenericRepr('<ExceptionInfo AttributeError("type object \'UserType\' has no attribute \'__schema__\'") tblen=2>')

snapshots['test_object_type_raises_error_when_defined_with_alias_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with aliases for fields not in GraphQL type: joinedDate') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_field_args_for_nonexisting_arg 1'] = GenericRepr('<ExceptionInfo ValueError("UserType class was defined with args mappings not in not in \'name\' field: arg") tblen=3>')

snapshots['test_object_type_raises_error_when_defined_with_field_args_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with fields args mappings for fields not in GraphQL type: group') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with __schema__ without GraphQL type') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_object_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UserType class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with __schema__ containing more than one GraphQL definition (found: ObjectTypeDefinitionNode, ObjectTypeDefinitionNode)') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_with_resolver_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with resolvers for fields not in GraphQL type: resolve_group') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_without_argument_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("UserType class was defined without required GraphQL definition for \'UserInput\' in __requires__") tblen=3>')

snapshots['test_object_type_raises_error_when_defined_without_extended_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendUserType graphql type was defined without required GraphQL type definition for \'User\' in __requires__") tblen=3>')

snapshots['test_object_type_raises_error_when_defined_without_fields 1'] = GenericRepr("<ExceptionInfo ValueError('UserType class was defined with __schema__ containing empty GraphQL type definition') tblen=3>")

snapshots['test_object_type_raises_error_when_defined_without_return_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("UserType class was defined without required GraphQL definition for \'Group\' in __requires__") tblen=3>')

snapshots['test_object_type_raises_error_when_extended_dependency_is_wrong_type 1'] = GenericRepr('<ExceptionInfo ValueError("ExampleType requires \'Example\' to be GraphQL type but other type was provided in \'__requires__\'") tblen=3>')
