# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_enum_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr('<ExceptionInfo ValueError("UserRoleEnum class was defined with __schema__ containing invalid GraphQL type definition for \'ScalarTypeDefinitionNode\' (expected \'enum\')") tblen=3>')

snapshots['test_enum_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'enom\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')

snapshots['test_enum_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UserRoleEnum class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_enum_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserRoleEnum class was defined with __schema__ containing more than one GraphQL definition (found: EnumTypeDefinitionNode, EnumTypeDefinitionNode)') tblen=3>")

snapshots['test_enum_type_raises_error_when_defined_without_schema 1'] = GenericRepr("<ExceptionInfo TypeError('UserRoleEnum class was defined without required __schema__ attribute') tblen=3>")

snapshots['test_enum_type_raises_error_when_dict_mapping_has_extra_items_not_in_definition 1'] = GenericRepr("<ExceptionInfo ValueError('UserRoleEnum class was defined with __enum__ containing extra items missing in GraphQL definition: REVIEW') tblen=3>")

snapshots['test_enum_type_raises_error_when_dict_mapping_misses_items_from_definition 1'] = GenericRepr("<ExceptionInfo ValueError('UserRoleEnum class was defined with __enum__ missing following items required by GraphQL definition: MOD') tblen=3>")

snapshots['test_enum_type_raises_error_when_enum_mapping_has_extra_items_not_in_definition 1'] = GenericRepr("<ExceptionInfo ValueError('UserRoleEnum class was defined with __enum__ containing extra items missing in GraphQL definition: REVIEW') tblen=3>")

snapshots['test_enum_type_raises_error_when_enum_mapping_misses_items_from_definition 1'] = GenericRepr("<ExceptionInfo ValueError('UserRoleEnum class was defined with __enum__ missing following items required by GraphQL definition: MOD') tblen=3>")
