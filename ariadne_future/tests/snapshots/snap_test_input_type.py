# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_input_type_raises_attribute_error_when_defined_without_schema 1'] = GenericRepr('<ExceptionInfo AttributeError("type object \'UserInput\' has no attribute \'__schema__\'") tblen=2>')

snapshots['test_input_type_raises_error_when_defined_with_args_map_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('UserInput class was defined with args for fields not in GraphQL input: fullName') tblen=3>")

snapshots['test_input_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserInput class was defined with __schema__ without GraphQL input') tblen=3>")

snapshots['test_input_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'inpet\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_input_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UserInput class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_input_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserInput class was defined with __schema__ containing more than one GraphQL definition (found: InputObjectTypeDefinitionNode, InputObjectTypeDefinitionNode)') tblen=3>")

snapshots['test_input_type_raises_error_when_defined_without_extended_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendUserInput graphql type was defined without required GraphQL type definition for \'User\' in __requires__") tblen=3>')

snapshots['test_input_type_raises_error_when_defined_without_field_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("UserInput class was defined without required GraphQL definition for \'Role\' in __requires__") tblen=3>')

snapshots['test_input_type_raises_error_when_defined_without_fields 1'] = GenericRepr("<ExceptionInfo ValueError('UserInput class was defined with __schema__ containing empty GraphQL input definition') tblen=3>")

snapshots['test_input_type_raises_error_when_extended_dependency_is_wrong_type 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendUserInput requires \'User\' to be GraphQL input but other type was provided in \'__requires__\'") tblen=3>')
