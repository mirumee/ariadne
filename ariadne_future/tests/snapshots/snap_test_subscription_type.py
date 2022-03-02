# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_subscription_type_raises_attribute_error_when_defined_without_schema 1'] = GenericRepr('<ExceptionInfo AttributeError("type object \'UsersSubscription\' has no attribute \'__schema__\'") tblen=3>')

snapshots['test_subscription_type_raises_error_when_defined_with_alias_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('ChatSubscription class was defined with aliases for fields not in GraphQL type: userAlerts') tblen=4>")

snapshots['test_subscription_type_raises_error_when_defined_with_invalid_graphql_type_name 1'] = GenericRepr('<ExceptionInfo ValueError("UsersSubscription class was defined with __schema__ containing GraphQL definition for \'type Other\' (expected \'type Subscription\')") tblen=4>')

snapshots['test_subscription_type_raises_error_when_defined_with_invalid_graphql_type_schema 1'] = GenericRepr("<ExceptionInfo ValueError('UsersSubscription class was defined with __schema__ without GraphQL type') tblen=4>")

snapshots['test_subscription_type_raises_error_when_defined_with_invalid_schema_str 1'] = GenericRepr('<ExceptionInfo GraphQLSyntaxError("Syntax Error: Unexpected Name \'typo\'.", locations=[SourceLocation(line=1, column=1)]) tblen=8>')

snapshots['test_subscription_type_raises_error_when_defined_with_invalid_schema_type 1'] = GenericRepr("<ExceptionInfo TypeError('UsersSubscription class was defined with __schema__ of invalid type: bool') tblen=4>")

snapshots['test_subscription_type_raises_error_when_defined_with_resolver_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('ChatSubscription class was defined with resolvers for fields not in GraphQL type: resolve_group') tblen=4>")

snapshots['test_subscription_type_raises_error_when_defined_with_sub_for_nonexisting_field 1'] = GenericRepr("<ExceptionInfo ValueError('ChatSubscription class was defined with subscribers for fields not in  GraphQL type: resolve_group') tblen=3>")

snapshots['test_subscription_type_raises_error_when_defined_without_argument_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ChatSubscription class was defined without required GraphQL definition for \'ChannelInput\' in __requires__") tblen=4>')

snapshots['test_subscription_type_raises_error_when_defined_without_extended_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendChatSubscription graphql type was defined without required GraphQL type definition for \'Subscription\' in __requires__") tblen=4>')

snapshots['test_subscription_type_raises_error_when_defined_without_fields 1'] = GenericRepr("<ExceptionInfo ValueError('UsersSubscription class was defined with __schema__ containing empty GraphQL type definition') tblen=4>")

snapshots['test_subscription_type_raises_error_when_defined_without_return_type_dependency 1'] = GenericRepr('<ExceptionInfo ValueError("ChatSubscription class was defined without required GraphQL definition for \'Chat\' in __requires__") tblen=4>')

snapshots['test_subscription_type_raises_error_when_extended_dependency_is_wrong_type 1'] = GenericRepr('<ExceptionInfo ValueError("ExtendChatSubscription requires \'Subscription\' to be GraphQL type but other type was provided in \'__requires__\'") tblen=4>')
