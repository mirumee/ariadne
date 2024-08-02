from unittest.mock import Mock

from graphql import default_field_resolver

from ariadne.resolvers import is_default_resolver, resolve_to


def test_alias_resolver_supports_callable_return_value():
    def callable_resolver(*_):
        return True

    obj = Mock(test=callable_resolver)
    alias_resolver = resolve_to("test")
    assert alias_resolver(obj, None)


def test_alias_resolver_supports_nested_name():
    parent_mapping = {"nested": {"hello": "world"}}
    parent_object = Mock(nested=Mock(hello="world"))

    alias_resolver = resolve_to("nested.hello")
    assert alias_resolver(parent_mapping, None) == "world"
    assert alias_resolver(parent_object, None) == "world"


def test_alias_resolver_passess_field_args_to_callable_return_value():
    def callable_resolver(*_, test):
        return test

    obj = Mock(test=callable_resolver)
    alias_resolver = resolve_to("test")
    assert alias_resolver(obj, None, test=True)


def test_alias_resolver_passess_default_resolver_check():
    alias_resolver = resolve_to("test")
    assert is_default_resolver(alias_resolver)


def test_graphql_core_default_resolver_passess_default_resolver_check():
    assert is_default_resolver(default_field_resolver)


def test_custom_resolver_fails_default_resolver_check():
    def custom_resolver(*_): ...  # pragma: no-cover

    assert not is_default_resolver(custom_resolver)
