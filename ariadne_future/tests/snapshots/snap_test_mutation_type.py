# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_mutation_type_raises_attribute_error_when_defined_without_schema 1'] = GenericRepr('<ExceptionInfo AttributeError("type object \'UserCreateMutation\' has no attribute \'__schema__\'") tblen=2>')

snapshots['test_mutation_type_raises_error_when_defined_for_different_type_name 1'] = GenericRepr('<ExceptionInfo ValueError("UserCreateMutation class was defined with __schema__ containing GraphQL definition for \'type User\' while \'type Mutation\' was expected") tblen=3>')

snapshots['test_mutation_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserCreateMutation class was defined with __schema__ without GraphQL type') tblen=3>")

snapshots['test_mutation_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UserCreateMutation class was defined with __schema__ of invalid type: bool') tblen=3>")

snapshots['test_mutation_type_raises_error_when_defined_with_multiple_fields 1'] = GenericRepr('<ExceptionInfo ValueError("UserCreateMutation class subclasses \'MutationType\' class which requires __schema__ to define exactly one field") tblen=3>')

snapshots['test_mutation_type_raises_error_when_defined_with_multiple_types_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UserCreateMutation class was defined with __schema__ containing more than one GraphQL definition (found: ObjectTypeDefinitionNode, ObjectTypeDefinitionNode)') tblen=3>")

snapshots['test_mutation_type_raises_error_when_defined_without_callable_resolve_mutation_attr 1'] = GenericRepr('<ExceptionInfo TypeError("UserCreateMutation class was defined with attribute \'resolve_mutation\' but it\'s not callable") tblen=3>')

snapshots['test_mutation_type_raises_error_when_defined_without_fields 1'] = GenericRepr("<ExceptionInfo ValueError('UserCreateMutation class was defined with __schema__ containing empty GraphQL type definition') tblen=3>")

snapshots['test_mutation_type_raises_error_when_defined_without_resolve_mutation_attr 1'] = GenericRepr('<ExceptionInfo AttributeError("UserCreateMutation class was defined without required \'resolve_mutation\' attribute") tblen=3>')

snapshots['test_mutation_type_raises_error_when_defined_without_return_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("UserCreateMutation class was defined without required GraphQL definition for \'UserCreateResult\' in __requires__") tblen=3>')

snapshots['test_object_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=7>')
