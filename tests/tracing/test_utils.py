from unittest.mock import Mock

from ariadne.contrib.tracing.utils import (
    format_path,
    is_introspection_field,
    should_trace,
)


def test_util_formats_info_path_value_into_reversed_list():
    path = Mock(
        key="username", prev=Mock(key="user", prev=Mock(key="users", prev=None))
    )
    assert format_path(path) == ["users", "user", "username"]


def test_introspection_check_returns_true_for_introspection_field():
    path = Mock(key="__type")
    info = Mock(path=path)
    assert is_introspection_field(info)


def test_introspection_check_returns_true_for_child_field_of_introspection_field():
    path = Mock(key="name", prev=Mock(key="__type"))
    info = Mock(path=path)
    assert is_introspection_field(info)


def test_introspection_check_returns_false_for_non_introspection_field():
    path = Mock(key="__type")
    info = Mock(path=path)
    assert is_introspection_field(info)


def test_introspection_check_returns_false_for__field():
    path = Mock(key="name", prev=Mock(key="user", prev=None))
    info = Mock(path=path)
    assert not is_introspection_field(info)


def test_introspection_field_is_excluded_from_tracing():
    path = Mock(key="__type")
    info = Mock(
        field_name="__type",
        path=path,
        parent_type=Mock(fields={"__type": Mock(resolve=True)}),
    )
    assert not should_trace(info)


def test_field_with_default_resolver_is_excluded_from_tracing_by_default():
    path = Mock(key="name", prev=Mock(key="user", prev=None))
    info = Mock(
        field_name="name",
        path=path,
        parent_type=Mock(fields={"name": Mock(resolve=None)}),
    )
    assert not should_trace(info)


def test_field_with_default_resolver_is_included_in_tracing_when_set():
    path = Mock(key="name", prev=Mock(key="user", prev=None))
    info = Mock(
        field_name="name",
        path=path,
        parent_type=Mock(fields={"name": Mock(resolve=None)}),
    )
    assert should_trace(info, trace_default_resolver=True)


def test_field_with_custom_resolver_is_included_in_tracing():
    path = Mock(key="name", prev=Mock(key="user", prev=None))
    info = Mock(
        field_name="name",
        path=path,
        parent_type=Mock(fields={"name": Mock(resolve=True)}),
    )
    assert should_trace(info)
