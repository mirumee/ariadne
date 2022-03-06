import pytest
from graphql import GraphQLError, build_schema

from ariadne import SchemaDirectiveVisitor

from ..directive_type import DirectiveType
from ..interface_type import InterfaceType
from ..object_type import ObjectType
from ..subscription_type import SubscriptionType


def test_subscription_type_raises_attribute_error_when_defined_without_schema(snapshot):
    with pytest.raises(AttributeError) as err:
        # pylint: disable=unused-variable
        class UsersSubscription(SubscriptionType):
            pass

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_invalid_schema_type(snapshot):
    with pytest.raises(TypeError) as err:
        # pylint: disable=unused-variable
        class UsersSubscription(SubscriptionType):
            __schema__ = True

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_invalid_schema_str(snapshot):
    with pytest.raises(GraphQLError) as err:
        # pylint: disable=unused-variable
        class UsersSubscription(SubscriptionType):
            __schema__ = "typo Subscription"

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_invalid_graphql_type_schema(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UsersSubscription(SubscriptionType):
            __schema__ = "scalar Subscription"

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_invalid_graphql_type_name(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UsersSubscription(SubscriptionType):
            __schema__ = "type Other"

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_without_fields(snapshot):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class UsersSubscription(SubscriptionType):
            __schema__ = "type Subscription"

    snapshot.assert_match(err)


def test_subscription_type_extracts_graphql_name():
    class UsersSubscription(SubscriptionType):
        __schema__ = """
        type Subscription {
            thread: ID!
        }
        """

    assert UsersSubscription.graphql_name == "Subscription"


def test_subscription_type_raises_error_when_defined_without_return_type_dependency(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ChatSubscription(SubscriptionType):
            __schema__ = """
            type Subscription {
                chat: Chat
                Chats: [Chat!]
            }
            """

    snapshot.assert_match(err)


def test_subscription_type_verifies_field_dependency():
    # pylint: disable=unused-variable
    class ChatType(ObjectType):
        __schema__ = """
        type Chat {
            id: ID!
        }
        """

    class ChatSubscription(SubscriptionType):
        __schema__ = """
        type Subscription {
            chat: Chat
            Chats: [Chat!]
        }
        """
        __requires__ = [ChatType]


def test_subscription_type_raises_error_when_defined_without_argument_type_dependency(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ChatSubscription(SubscriptionType):
            __schema__ = """
            type Subscription {
                chat(input: ChannelInput): [String!]!
            }
            """

    snapshot.assert_match(err)


def test_subscription_type_can_be_extended_with_new_fields():
    # pylint: disable=unused-variable
    class ChatSubscription(SubscriptionType):
        __schema__ = """
        type Subscription {
            chat: ID!
        }
        """

    class ExtendChatSubscription(SubscriptionType):
        __schema__ = """
        extend type Subscription {
            thread: ID!
        }
        """
        __requires__ = [ChatSubscription]


def test_subscription_type_can_be_extended_with_directive():
    # pylint: disable=unused-variable
    class ExampleDirective(DirectiveType):
        __schema__ = "directive @example on OBJECT"
        __visitor__ = SchemaDirectiveVisitor

    class ChatSubscription(SubscriptionType):
        __schema__ = """
        type Subscription {
            chat: ID!
        }
        """

    class ExtendChatSubscription(SubscriptionType):
        __schema__ = "extend type Subscription @example"
        __requires__ = [ChatSubscription, ExampleDirective]


def test_subscription_type_can_be_extended_with_interface():
    # pylint: disable=unused-variable
    class ExampleInterface(InterfaceType):
        __schema__ = """
        interface Interface {
            threads: ID!
        }
        """

    class ChatSubscription(SubscriptionType):
        __schema__ = """
        type Subscription {
            chat: ID!
        }
        """

    class ExtendChatSubscription(SubscriptionType):
        __schema__ = """
        extend type Subscription implements Interface {
            threads: ID!
        }
        """
        __requires__ = [ChatSubscription, ExampleInterface]


def test_subscription_type_raises_error_when_defined_without_extended_dependency(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExtendChatSubscription(SubscriptionType):
            __schema__ = """
            extend type Subscription {
                thread: ID!
            }
            """

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_extended_dependency_is_wrong_type(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ExampleInterface(InterfaceType):
            __schema__ = """
            interface Subscription {
                id: ID!
            }
            """

        class ExtendChatSubscription(SubscriptionType):
            __schema__ = """
            extend type Subscription {
                thread: ID!
            }
            """
            __requires__ = [ExampleInterface]

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_alias_for_nonexisting_field(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ChatSubscription(SubscriptionType):
            __schema__ = """
            type Subscription {
                chat: ID!
            }
            """
            __aliases__ = {
                "userAlerts": "user_alerts",
            }

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_resolver_for_nonexisting_field(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ChatSubscription(SubscriptionType):
            __schema__ = """
            type Subscription {
                chat: ID!
            }
            """

            def resolve_group(*_):
                return None

    snapshot.assert_match(err)


def test_subscription_type_raises_error_when_defined_with_sub_for_nonexisting_field(
    snapshot,
):
    with pytest.raises(ValueError) as err:
        # pylint: disable=unused-variable
        class ChatSubscription(SubscriptionType):
            __schema__ = """
            type Subscription {
                chat: ID!
            }
            """

            def subscribe_group(*_):
                return None

    snapshot.assert_match(err)


def test_subscription_type_binds_resolver_and_subscriber_to_schema():
    schema = build_schema(
        """
            type Query {
                hello: String
            }

            type Subscription {
                chat: ID!
            }
        """
    )

    class ChatSubscription(SubscriptionType):
        __schema__ = """
        type Subscription {
            chat: ID!
        }
        """

        def resolve_chat(*_):
            return None

        def subscribe_chat(*_):
            return None

    ChatSubscription.__bind_to_schema__(schema)

    field = schema.type_map.get("Subscription").fields["chat"]
    assert field.resolve is ChatSubscription.resolve_chat
    assert field.subscribe is ChatSubscription.subscribe_chat
